import collections
import contextlib
import functools
import inspect
from typing import Generator, List, Optional

from .utils import optional_args_func


class Handler:
    """
    Unbound handler.

    See also BoundHandler.
    """

    def __init__(self, func, hook):
        if isinstance(func, classmethod):
            raise TypeError('Handler cannot be a classmethod, {} is one'.format(func))
        if isinstance(func, staticmethod):
            raise TypeError('Handler cannot be a staticmethod, {} is one'.format(func))
        if not callable(func):
            raise TypeError('{} should be a callable'.format(func))

        if isinstance(func, Handler):
            func = func._original_func

        if isinstance(func, functools.partial):
            func_name = func.func.__name__
        else:
            func_name = func.__name__

        self.__name__ = func_name
        self.name = func_name
        self.hook_name = hook.name

        if hook.args:
            func_sig = inspect.signature(func)
            for param in func_sig.parameters:
                if param in ('self', 'cls'):
                    continue
                if param not in hook.args:
                    raise RuntimeError('{} is not a valid handler for {}, argument {!r} is not supported'.format(
                        func, hook, param
                    ))

        self._original_func = func
        self._optional_args_func = optional_args_func(self._original_func)
        self.is_generator = inspect.isgeneratorfunction(func)

    def __call__(_self_, **kwargs):
        return _self_._optional_args_func(**kwargs)

    def __repr__(self):
        return 'Handler({!r})'.format(self._original_func)


class BoundHandler(Handler):
    """
    Handler associated with a Hook.
    Created when requesting a hook's handlers by associating unbound handlers with the hook.
    """
    def __init__(self, hook: 'Hook', handler: Handler):
        self.hook = hook
        if isinstance(handler, BoundHandler):
            self._handler = handler._handler
        else:
            self._handler = handler

    def __getattribute__(self, name):
        if name in ('hook', '_handler'):
            return object.__getattribute__(self, name)
        else:
            return getattr(self._handler, name)

    def __setattr__(self, name, value):
        if name in ('hook', '_handler'):
            object.__setattr__(self, name, value)
        else:
            raise AttributeError(name)

    def __call__(_self_, **kwargs):
        kwargs.setdefault('hook', _self_.hook)

        if _self_.hook.is_class_associated:
            kwargs.setdefault('cls', _self_.hook.subject)
        elif _self_.hook.is_instance_associated:
            kwargs.setdefault('self', _self_.hook.subject)

        with _self_.hook._triggering_ctx():
            if _self_._handler.is_generator and _self_.hook.consume_generators:
                return list(_self_._handler(**kwargs))
            else:
                return _self_._handler(**kwargs)


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
    A hook is something that a user can hook into.

    It may have a name, a subject. To hook into it, user registers handlers with it.

    When a thing has hooks, it means one can interact with this thing via hooks.
    This thing that the hook is providing a way to interact with, is here called the hook's subject.

    Hook's handlers are functions registered to be called when the hook is triggered (called)
    most often by hook's subject itself.
    """
    def __init__(
        self, name=None, subject=None,
        parent_class_hook=None, instance_class_hook=None, single_handler=False,
        defining_class=None,
        args=None,
        consume_generators=True,
    ):
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

        self.args = tuple(args) if args else ()

        # If the underlying handler function is a generator, it will be consumed when calling the handler.
        # Set consume_generators to False to disable this behaviour.
        self.consume_generators = consume_generators

        self._direct_handlers = []
        self._cached_handlers = None

        self._is_triggering = False

    def __call__(self, func) -> callable:
        return self.register_handler(func)

    @contextlib.contextmanager
    def _triggering_ctx(self):
        """
        Context manager that ensures that a hook is not re-triggered by one of its handlers.
        """
        if self._is_triggering:
            raise RuntimeError('{} cannot be triggered while it is being handled'.format(self))
        self._is_triggering = True
        try:
            yield self
        finally:
            self._is_triggering = False

    def trigger(_self_, **kwargs):
        if _self_.args:
            for k in kwargs.keys():
                if not k.startswith('_') and k not in _self_.args:
                    raise ValueError('Unexpected keyword argument {!r} for {}'.format(k, _self_))

        if _self_.single_handler:
            if _self_.last_handler:
                return _self_.last_handler(**kwargs)
            else:
                return None

        results = []
        for handler in _self_.handlers:
            result = handler(**kwargs)
            results.append(result)
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
        def get_raw_handlers():
            if self.parent_class_hook is not None:
                yield from self.parent_class_hook.get_all_handlers()
            if self.instance_class_hook is not None:
                yield from self.instance_class_hook.get_all_handlers()
            yield from self._direct_handlers

        yield from (BoundHandler(self, h) for h in get_raw_handlers())

    @property
    def handlers(self) -> List[BoundHandler]:
        if self._cached_handlers is None:
            self._cached_handlers = list(self.get_all_handlers())
        return self._cached_handlers

    @property
    def last_handler(self) -> Optional[BoundHandler]:
        if self.handlers:
            return self.handlers[-1]
        else:
            return None

    def register_handler(self, handler_func) -> Handler:
        handler = Handler(handler_func, hook=self)
        self._direct_handlers.append(handler)
        self._cached_handlers = None
        return handler

    def has_handler(self, handler_or_func) -> bool:
        for handler in self._direct_handlers:
            if handler is handler_or_func or handler._original_func is handler_or_func:
                return True

        if self.parent_class_hook is not None and self.parent_class_hook.has_handler(handler_or_func):
            return True

        if self.instance_class_hook is not None and self.instance_class_hook.has_handler(handler_or_func):
            return True

        return False

    def unregister_handler(self, handler_or_func):
        """
        Remove the handler from this hook's list of handlers.
        This does not give up until the handler is found in the class hierarchy.
        """
        index = -1
        for i, handler in enumerate(self._direct_handlers):
            if handler is handler_or_func or handler._original_func is handler_or_func:
                index = i
                break
        if index >= 0:
            self._direct_handlers.pop(index)
            self._cached_handlers = None

        elif self.parent_class_hook is not None and self.parent_class_hook.has_handler(handler_or_func):
            self.parent_class_hook.unregister_handler(handler_or_func)
            self._cached_handlers = None

        elif self.instance_class_hook is not None and self.instance_class_hook.has_handler(handler_or_func):
            self.instance_class_hook.unregister_handler(handler_or_func)
            self._cached_handlers = None

        else:
            raise ValueError('{} is not a registered handler of {}'.format(handler_or_func, self))

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

    def create_hook(_self_, **kwargs):
        kwargs.setdefault('name', _self_.name)
        kwargs.setdefault('defining_class', _self_.defining_class)
        kwargs.setdefault('args', _self_.defining_hook.args)
        hook = _self_.hook_cls(**kwargs)

        # [H002]
        # copy the handlers from the defining hook -- if handlers are registered
        # right next to the hook declaration in a class body then these handlers
        # would otherwise be lost because of the Hook -> HookDescriptor -> Hook overwrite.
        if hook.is_class_associated:
            for handler in _self_.defining_hook._direct_handlers:
                hook.register_handler(handler._original_func)

        return hook

    def __str__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, self.name)

    __repr__ = __str__


class ClassHook(Hook):
    """
    A class hook is associated with a particular class. By default, a separate hook is generated
    automatically for every class derived from this class, however, the derived class hook inherits
    all handlers registered with the parent class's corresponding hook. Referencing a class hook
    from an instance of the class raises ``TypeError``. Class hooks are just hooks that use class they belong
    to as a namespace. When you create a new class with a hookable class as its base class, the new class
    will inherit all the handlers registered with hooks of the parent class.
    """
    def trigger(_self_, **kwargs):
        if not _self_.is_class_associated:
            raise TypeError('Incorrect usage of {}'.format(_self_))
        return super().trigger(**kwargs)

    def register_handler(self, handler_func):
        if self.is_instance_associated:
            raise TypeError('Incorrect usage of {}'.format(self))
        return super().register_handler(handler_func)


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

    def trigger(_self_, **kwargs):
        if not _self_.defining_class:
            raise RuntimeError((
                'Did you forget to decorate your hookable class? {} is not initialised properly.'
            ).format(_self_))

        if not _self_.is_instance_associated:
            raise TypeError('Incorrect usage of {}'.format(_self_))

        return super().trigger(**kwargs)


class HookableMeta(type):
    @classmethod
    def __prepare__(meta, name, bases):
        # If you register multiple attributes of a class as handlers of the same hook within the same class body then
        # their order must be preserved.
        # This method is required only for Python 3.5.
        return collections.OrderedDict()

    def __new__(meta, name, bases, dct):

        for parent in bases:
            for k, v in dct.items():
                if isinstance(v, Handler) and isinstance(getattr(parent, k, None), Hook):
                    raise RuntimeError('{}.{} (handler) overwrites hook with the same name'.format(name, k))

        # [H001]
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
                    if not v.hook_name:
                        # [H002]
                        # Ignore the handlers that are registered against just-declared hooks who
                        # don't have name set yet.
                        continue
                    parent_hook = getattr(hookable_parent, v.hook_name, None)  # type: Hook
                    if parent_hook is not None and parent_hook.has_handler(v):
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
