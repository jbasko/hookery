import collections
import inspect
from typing import Generator, List

from .utils import optional_args_func


class Handler:
    def __init__(self, func, hook):
        if isinstance(func, classmethod):
            raise TypeError('Handler cannot be a classmethod, {} is one'.format(func))
        if isinstance(func, staticmethod):
            raise TypeError('Handler cannot be a staticmethod, {} is one'.format(func))
        if not callable(func):
            raise TypeError('{} should be a callable'.format(func))
        self.__name__ = func.__name__
        self.name = func.__name__
        self.hook_name = hook.name
        self._original_func = func
        self._optional_args_func = optional_args_func(self._original_func)
        self.is_generator = inspect.isgeneratorfunction(func)

    def __call__(self, *, _handler_context=None, **kwargs):
        # _handler_context is how "self" and "cls" can be passed to handler function
        # without being consumed by hookery's implementation.
        _handler_context = _handler_context or {}
        return self._optional_args_func(**_handler_context, **kwargs)

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
    def __init__(
        self, name=None, subject=None,
        parent_class_hook=None, instance_class_hook=None, single_handler=False,
        defining_class=None,
    ):
        if self.__class__ is Hook:
            raise TypeError('{} instances should not be created, choose one of the flavours'.format(Hook))

        self.name = name
        self.subject = subject if subject is not None else NoSubject()

        # Hook associated with the parent class of the class which is this hook's subject
        self.parent_class_hook = parent_class_hook  # type: Hook

        # Hook associated with the class of the instance which is this hook's subject
        self.instance_class_hook = instance_class_hook  # type: Hook

        # Class in which the hook was defined.
        self.defining_class = defining_class  # type: type

        # If a hook is marked as single handler, only its last registered handler will be called on trigger.
        self.single_handler = single_handler  # type: bool

        self._direct_handlers = []
        self._cached_handlers = None

    def __call__(self, func) -> callable:
        return self.register_handler(func)

    def trigger(self, **kwargs):
        if self.single_handler:
            if self.last_handler:
                return self.get_result_from_handler(self.last_handler, **kwargs)
            else:
                return None

        results = []
        for handler in self.handlers:
            results.append(self.get_result_from_handler(handler, **kwargs))
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
        handler = Handler(handler, hook=self)
        self._direct_handlers.append(handler)
        self._cached_handlers = None
        return handler

    def unregister_handler(self, handler):
        """
        Remove the handler from this hook's list of handlers.
        This does not give up until the handler is found in the class hierarchy.
        """
        if handler in self._direct_handlers:
            self._direct_handlers.remove(handler)
            self._cached_handlers = None

        elif self.parent_class_hook is not None and handler in self.parent_class_hook.handlers:
            self.parent_class_hook.unregister_handler(handler)
            self._cached_handlers = None

        elif self.instance_class_hook is not None and handler in self.instance_class_hook.handlers:
            self.instance_class_hook.unregister_handler(handler)
            self._cached_handlers = None

        else:
            raise ValueError('{} is not a registered handler of {}'.format(handler, self))

    def call_handler(self, handler, **kwargs):
        """
        Call handler correctly by passing the right handler context.
        If you call handler directly, you are responsible for passing the right "self" and "cls"
        values (if required) which can only be done via _handler_context kwarg as otherwise
        "self" and "cls" might be consumed by hookery's internals.
        """
        handler_context = {}
        if self.is_class_associated:
            handler_context['cls'] = self.subject
        elif self.is_instance_associated:
            handler_context['self'] = self.subject
        return handler(_handler_context=handler_context, **kwargs)

    def get_result_from_handler(self, handler, **kwargs):
        """
        Get result from handler correctly by passing the right handler context.
        See call_handler.
        """
        result = self.call_handler(handler, **kwargs)
        if handler.is_generator:
            return list(result)
        else:
            return result

    def __bool__(self):
        return bool(self.handlers)

    @property
    def is_class_associated(self):
        return isinstance(self.subject, type)

    @property
    def is_instance_associated(self):
        return self.subject is not None and not isinstance(self.subject, (type, NoSubject))

    def __repr__(self):
        if self.is_class_associated:
            return '<{} {}.{}>'.format(self.__class__.__name__, self.subject.__name__, self.name)
        else:
            return '<{} {}.{}>'.format(self.__class__.__name__, self.subject.__class__.__name__, self.name)

    __str__ = __repr__


class HookDescriptor:
    def __init__(self, defining_hook: Hook, defining_class: type):
        self.defining_hook = defining_hook

        # the class which defined the hook
        self.defining_class = defining_class

    @property
    def name(self):
        return self.defining_hook.name

    @property
    def hook_cls(self):
        return self.defining_hook.__class__

    def __get__(self, instance, owner):
        has_class_as_subject = instance is None
        if has_class_as_subject:
            attr_name = '_class_{}_hook#{}'.format(owner.__name__, self.name)
            if not hasattr(owner, attr_name):
                parent_class_hook = getattr(owner.__bases__[0], self.name, None)
                if parent_class_hook is not None and parent_class_hook.defining_class != self.defining_class:
                    # Do not link to parent_class_hook if it is actually
                    # a different hook (this hook is an overwrite of it).
                    parent_class_hook = None
                setattr(owner, attr_name, self.create_hook(
                    subject=owner,
                    parent_class_hook=parent_class_hook,
                    **self.defining_hook.meta
                ))
            return getattr(owner, attr_name)
        else:
            attr_name = '_instance_hook#{}'.format(self.name)
            if not hasattr(instance, attr_name):
                setattr(instance, attr_name, self.create_hook(
                    subject=instance,
                    instance_class_hook=getattr(owner, self.name),
                    **self.defining_hook.meta
                ))
            return getattr(instance, attr_name)

    def create_hook(self, **kwargs):
        kwargs.setdefault('name', self.name)
        kwargs.setdefault('defining_class', self.defining_class)
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
    def trigger(self, **kwargs):
        if not self.is_class_associated:
            raise TypeError('Incorrect usage of {}'.format(self))
        return super().trigger(**kwargs)

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

    def trigger(self, **kwargs):
        if not self.is_instance_associated:
            raise TypeError('Incorrect usage of {}'.format(self))

        kwargs.setdefault('_hook_subject', self.subject)

        return super().trigger(**kwargs)


class HookableMeta(type):
    @classmethod
    def __prepare__(meta, name, bases):
        # This is to preserve the class attribute declaration order in Python 3.5
        return collections.OrderedDict()

    def __new__(meta, name, bases, dct):

        for parent in bases:
            for k, v in dct.items():
                if isinstance(v, Handler) and isinstance(getattr(parent, k, None), Hook):
                    raise RuntimeError('{}.{} (handler) overwrites hook with the same name'.format(name, k))

        # Find handlers registered in the class against parent class's hooks.
        # We interpret it as attempt to register handlers for current class hook not for parent class hook.

        hookable_parent = None
        handlers_registered_with_parent_class_hook = []
        for base in bases:
            if issubclass(base, Hookable):
                hookable_parent = base
        if hookable_parent is not None:
            for k, v in list(dct.items()):
                if isinstance(v, Handler):
                    parent_hook = getattr(hookable_parent, v.hook_name, None)  # type: Hook
                    if parent_hook is not None and v in parent_hook.handlers:
                        parent_hook.unregister_handler(v)
                        handlers_registered_with_parent_class_hook.append((v.hook_name, v._original_func))

        hook_definitions = []

        for k, v in list(dct.items()):
            if isinstance(v, (ClassHook, InstanceHook)):
                dct.pop(k)
                if v.name is None:
                    v.name = k
                hook_definitions.append((k, v))

        cls = super().__new__(meta, name, bases, dct)

        for k, v in hook_definitions:
            setattr(cls, k, HookDescriptor(defining_hook=v, defining_class=cls))

        for k, v in handlers_registered_with_parent_class_hook:
            getattr(cls, k)(v)

        return cls


class Hookable(metaclass=HookableMeta):
    pass


def hookable(cls):
    """
    Initialise hookery in a class that declares hooks by decorating it with this decorator.

    This replaces the class with another one which has the same name, but also inherits Hookable
    which has HookableMeta set as metaclass so that sub-classes of cls will have hook descriptors
    initialised properly.

    When you say:
        @hookable
        class My:
            before = Hook()

    then @hookable changes My.before to be a HookDescriptor which is then
    changed into Hook if anyone accesses it.

    There is no need to decorate sub-classes of cls with @hookable.
    """
    assert isinstance(cls, type)

    # For classes that won't have descriptors initialised by metaclass, need to do it here.
    hook_definitions = []
    if not issubclass(cls, Hookable):
        for k, v in list(cls.__dict__.items()):
            if isinstance(v, (ClassHook, InstanceHook)):
                delattr(cls, k)
                if v.name is None:
                    v.name = k
                hook_definitions.append((k, v))

    hookable_cls = type(cls.__name__, (cls, Hookable), {})

    for k, v in hook_definitions:
        setattr(hookable_cls, k, HookDescriptor(defining_hook=v, defining_class=hookable_cls))

    return hookable_cls
