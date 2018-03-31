import inspect
from typing import Generator, List

from .utils import optional_args_func


class Handler:
    def __init__(self, func):
        if isinstance(func, classmethod):
            raise TypeError('Handler cannot be a classmethod, {} is one'.format(func))
        if isinstance(func, staticmethod):
            raise TypeError('Handler cannot be a staticmethod, {} is one'.format(func))
        if not callable(func):
            raise TypeError('{} should be a callable'.format(func))
        self.__name__ = func.__name__
        self.name = func.__name__
        self._original_func = func
        self._optional_args_func = optional_args_func(self._original_func)
        self.is_generator = inspect.isgeneratorfunction(func)

    def __call__(self, *args, **kwargs):
        return self._optional_args_func(*args, **kwargs)

    def get_result(self, *args, **kwargs):
        if self.is_generator:
            return list(self(*args, **kwargs))
        else:
            return self(*args, **kwargs)

    def __repr__(self):
        return 'Handler({!r})'.format(self._original_func)


class NoSubject:
    """
    Represents a placeholder object used as subject of a free hook
    which isn't associated with any class or object.
    """
    def __str__(self):
        return self.__class__.__name__

    __repr__ = __str__


class Hook:
    """
    A hook is something that has a name, has a subject, and may have handlers
    registered with it.

    When a thing has hooks, it means one can interact with this thing via hooks.
    This thing that the hook is providing a way to interact with, is here called the hook's subject.

    Hook's handlers are functions registered to be called when the hook is triggered (called)
    most often by hook's subject itself.

    When there is no explicit subject for a hook, it is like a global event that you can register
    listeners to.
    """
    def __init__(self, name=None, subject=None, parent_class_hook=None, instance_class_hook=None, single_handler=False):
        if self.__class__ is Hook:
            raise TypeError('{} instances should not be created, choose one of the flavours'.format(Hook))

        self.name = name
        self.subject = subject if subject is not None else NoSubject()

        # Hook associated with the parent class of the class which is this hook's subject
        self.parent_class_hook = parent_class_hook

        # Hook associated with the class of the instance which is this hook's subject
        self.instance_class_hook = instance_class_hook

        # If a hook is marked as single handler, only its last registered handler will be called on trigger.
        self.single_handler = single_handler

        self._direct_handlers = []
        self._cached_handlers = None

    def __call__(self, func) -> callable:
        return self.register_handler(func)

    def trigger(self, *args, **kwargs):
        if self.single_handler:
            if self.last_handler:
                return self.last_handler.get_result(*args, **kwargs)
            else:
                return None

        results = []
        for handler in self.handlers:
            results.append(handler.get_result(*args, **kwargs))
        return results

    @property
    def meta(self):
        """
        A dictionary of meta information describing the nature of this hook,
        to be passed as kwargs to Hook initialiser when creating a hook based on an existing hook.
        """
        return {
            'single_handler': self.single_handler,
        }

    def get_all_handlers(self) -> Generator[Handler, None, None]:
        if self.parent_class_hook is not None:
            yield from self.parent_class_hook.get_all_handlers()
        if self.instance_class_hook is not None:
            yield from self.instance_class_hook.get_all_handlers()
        yield from self._direct_handlers

    @property
    def handlers(self) -> List[Handler]:
        if self._cached_handlers is None:
            self._cached_handlers = list(self.get_all_handlers())
        return self._cached_handlers

    @property
    def last_handler(self):
        if self.handlers:
            return self.handlers[-1]
        else:
            return None

    def register_handler(self, handler) -> Handler:
        self._direct_handlers.append(Handler(handler))
        self._cached_handlers = None
        return handler

    def __bool__(self):
        return bool(self.handlers)

    @property
    def is_class_associated(self):
        return isinstance(self.subject, type)

    @property
    def is_instance_associated(self):
        return self.subject is not None and not isinstance(self.subject, (type, NoSubject))


class HookDescriptor:
    def __init__(self, base_hook: Hook):
        self.base_hook = base_hook

    @property
    def name(self):
        return self.base_hook.name

    @property
    def subject(self):
        return self.base_hook.subject

    @property
    def hook_cls(self):
        return self.base_hook.__class__

    def __get__(self, instance, owner):
        has_class_as_subject = instance is None
        if has_class_as_subject:
            attr_name = '_class_{}_hook#{}'.format(owner.__name__, self.name)
            if not hasattr(owner, attr_name):
                setattr(owner, attr_name, self.create_hook(
                    subject=owner,
                    parent_class_hook=getattr(owner.__bases__[0], self.name, None),
                    **self.base_hook.meta
                ))
            return getattr(owner, attr_name)
        else:
            attr_name = '_instance_hook#{}'.format(self.name)
            if not hasattr(instance, attr_name):
                setattr(instance, attr_name, self.create_hook(
                    subject=instance,
                    instance_class_hook=getattr(owner, self.name),
                    **self.base_hook.meta
                ))
            return getattr(instance, attr_name)

    def create_hook(self, **kwargs):
        kwargs.setdefault('name', self.name)
        return self.hook_cls(**kwargs)

    def __str__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, self.name)

    __repr__ = __str__


class GlobalHook(Hook):
    """
    Global hooks are just events in global scope that user can subscribe to (register handlers with)
    and can trigger from anywhere without any context. They don’t necessarily have to be global,
    but they are unless user manages the scope.
    """
    def __init__(self, name=None, **kwargs):
        if not name:
            raise ValueError('{}.name is required'.format(self.__class__.__name__))
        super().__init__(name=name, subject=NoSubject(), **kwargs)


class ClassHook(Hook):
    """
    A class hook is associated with a particular class. By default, a separate hook is generated
    automatically for every class derived from this class, however, the derived class hook inherits
    all handlers registered with the parent class's corresponding hook. Referencing a class hook
    from an instance of the class raises ``TypeError``. Class hooks are just hooks that use class they belong
    to as a namespace. When you create a new class with a hookable class as its base class, the new class
    will inherit all the handlers registered with hooks of the parent class.
    """
    def trigger(self, *args, **kwargs):
        if not self.is_class_associated:
            raise TypeError('Incorrect usage of {}'.format(self))
        return super().trigger(*args, **kwargs)

    def register_handler(self, handler):
        if self.is_instance_associated:
            raise TypeError('Incorrect usage of {}'.format(self))
        return super().register_handler(handler)


class InstanceHook(Hook):
    """
    An instance hook is associated with a hookable class, but a separate instance-associated hook is
    auto-generated for each instance of this class. That way handlers can be registered separately with the
    class-associated hook (to affect all instances of the class) and with the instance-associated hook
    (to only affect the particular instance). Unlike with class hooks which are triggered against a particular
    class, an instance hook can only be triggered with a particular instance in context, triggering such hook
    on class will raise a ``TypeError``.
    When an instance hook is triggered, all handlers registered with the class-associated hook will be
    called first and then all handlers for the instance-associated hook will be called.
    """

    def trigger(self, *args, **kwargs):
        if not self.is_instance_associated:
            raise TypeError('Incorrect usage of {}'.format(self))

        # Instance hook handlers can always rely on instance
        # being passed in.
        if not args or self.subject not in args:
            args = (self.subject,) + args

        return super().trigger(*args, **kwargs)


def hookable(cls):
    """
    Initialise hookery in a class that declares hooks by decorating it with this decorator.
    This is an alternative to using a metaclass or a specific base class.

    When you say:
        @hookable
        class My:
            before = Hook()

    then @hookable changes My.before to be a HookDescriptor which is then
    changed into Hook if anyone accesses it.

    To enable hooks in sub-classes of a hookable class, each sub-class must be decorated too.
    """
    assert isinstance(cls, type)

    for k, v in list(cls.__dict__.items()):
        if isinstance(v, (ClassHook, InstanceHook)):
            if v.name is None:
                v.name = k
            if v.subject is None:
                v.subject = cls
            setattr(cls, k, HookDescriptor(base_hook=v))

    return cls
