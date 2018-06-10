import abc
import collections
from typing import Union

from hookery.utils import optional_args_func


class AbstractHook(abc.ABC):
    """
    Events happen to objects. Events that can be listened to and used to hook into execution
    of some algorithm are called hooks.

    To hook into a hook, one registers a hook handler. Handlers can be associated with a context
    explicitly, implicitly, or even be not associated with any context in which case they are called
    whenever the event happens irrespective of who it happens to.
    """

    @abc.abstractmethod
    def trigger(self, ctx, *args, **kwargs):
        """
        `ctx` is the object on which the event is happening; it is used to
        determine the class whose handlers should be invoked. It is also
        passed as the first positional argument to the handlers.
        """
        raise NotImplementedError()

    def __call__(self, ctx=None, *args, **kwargs):
        """
        Calling a hook instance should create a decorator that registers handlers
        associated with `ctx` passed to `__call__`.

        Calling without any `ctx` creates a decorator that registers a global handler.
        A global handler is called irrespective of context in which the event happens.
        """
        raise NotImplementedError()


class Hook(AbstractHook):
    """
    Represents an unbound hook.

    A hook is unbound before it is associated with a hook specification -- an instance of :class:`HookSpec`.
    """

    def __init__(self, name: str=None):
        self.name = name

    def __get__(self, instance, owner) -> Union['BoundHook', 'Hook']:
        if instance is None:
            return self
        else:
            if not hasattr(instance, self._attr_name):
                setattr(instance, self._attr_name, BoundHook(self.name, spec=instance))
            return getattr(instance, self._attr_name)

    def __set_name__(self, owner, name):  # Python 3.6+
        owner.name = name

    def __repr__(self):
        return '<{} {!r}>'.format(
            self.__class__.__name__,
            self.name
        )

    def trigger(self, ctx, *args, **kwargs):
        """
        Unbound :class:`Hook` instances should not be triggered.
        """
        raise RuntimeError('{} instance should not be triggered'.format(self.__class__))

    def __call__(self, ctx=None, *args, **kwargs):
        raise RuntimeError(
            'Handler registration decorators should only be '
            'created for hooks bound to a hook specification.'
        )

    @property
    def _attr_name(self):
        """
        Name under which this hook is stored in the ``__dict__`` of :class:`HookSpec` instance.
        """
        return 'hook#{}'.format(self.name)


class BoundHook(AbstractHook):
    """
    A hook that is bound to an instance of hook specification.

    See :class:`Hook`.
    """
    def __init__(self, name: str, spec: 'HookSpec'):
        self.name = name
        self.spec = spec  # type: HookSpec

    def __call__(self, ctx):
        """
        Creates a handler registration function against the ctx object --
        the returned function can be used to register a handler of this hook on the ctx object.
        """
        def register_handler(f):
            self.spec._register_handler(self.name, f, ctx=ctx)

        return register_handler

    def trigger(self, ctx, *args, **kwargs):
        return self.spec._get_trigger(self.name, ctx)(ctx, *args, **kwargs)


class HookSpecMeta(type):
    @classmethod
    def __prepare__(metacls, name, bases):
        # To preserve attribute declaration order in Python 3.5
        return collections.OrderedDict()

    def __new__(meta, name, bases, dct):
        """
        Hooks can be declared in two ways:
        1) as methods of a HookSpec class.
        2) as HookDescriptor's declared in a HookSpec class.

        If a hook is declared as a method, we must replace it with a HookDescriptor here.
        If declared as a descriptor, we must set its name here.
        """

        clean_dct = collections.OrderedDict()
        clean_dct['hooks'] = collections.OrderedDict()

        for k, v in dct.items():
            if isinstance(v, Hook):
                # Hook declared as a descriptor
                if v.name is None:
                    # Set name for a hook declared as a nameless descriptor
                    v.name = k

                clean_dct[k] = v
                clean_dct['hooks'][k] = v

            elif callable(v) and not k.startswith('_'):
                # Hook declared as a method, must replace with a descriptor
                hook_descr = Hook(k)
                clean_dct[k] = hook_descr
                clean_dct['hooks'][k] = hook_descr

            else:
                # Normal attribute
                clean_dct[k] = v

        return super().__new__(meta, name, bases, clean_dct)


def get_handler_marker(handler):
    marker = getattr(handler, '_hookery_marker', None)
    if marker is None:
        marker = []
    return marker


def set_handler_marker(handler, marker):
    setattr(handler, '_hookery_marker', marker)


def add_to_handler_marker(handler, hook_name):
    marker = get_handler_marker(handler)
    marker.append(hook_name)
    set_handler_marker(handler, marker)


def handles_hook(handler, hook_name):
    return hook_name in get_handler_marker(handler)


class HookSpec(metaclass=HookSpecMeta):
    """
    Hook specification. Also acts as a hook handler registry.
    TODO Remove this feature so we can have public methods:
    All methods of HookSpec whose name does not start with "_" are hooks.
    """
    def __init__(self):
        self._ctx_specific_handlers = collections.defaultdict(list)
        self._triggers = {}

    def _register_handler(self, hook_name, handler, ctx=None):
        if hook_name not in self.hooks:
            raise ValueError('Unknown hook {!r}'.format(hook_name))

        # Mark the handler so we can distinguish it from methods that just happen to have the same name,
        # but aren't marked as handlers.
        add_to_handler_marker(handler, hook_name)

        assert handles_hook(handler, hook_name)

        # We only store handlers that are associated with a ctx object.
        if ctx is not None:
            self._ctx_specific_handlers[(ctx, hook_name)].append(optional_args_func(handler))

    def _get_handlers(self, hook_name, ctx):
        handlers = []

        # Handlers associated with classes in the class tree of the ctx object
        for base in reversed(type(ctx).__mro__[:-1]):
            if hook_name in base.__dict__:
                handler = base.__dict__[hook_name]
                if handles_hook(handler, hook_name):
                    handlers.append(handler)

        # Handlers associated with the individual ctx object
        handlers.extend(self._ctx_specific_handlers[(ctx, hook_name)])

        return handlers

    def _get_trigger(self, hook_name, ctx):
        trigger_key = (hook_name, ctx)
        if trigger_key not in self._triggers:
            def trigger(*args, **kwargs):
                results = [h(*args, **kwargs) for h in self._get_handlers(hook_name, ctx)]
                return results
            self._triggers[trigger_key] = trigger
        return self._triggers[trigger_key]

    def __call__(self, f):
        """
        Decorator for functions and methods whose name tells which hook they are handling.
        The decorated function is replaced with a trigger for the hook!
        """
        hook_name = f.__name__
        self._register_handler(hook_name, f)
        return f

    @classmethod
    def _merge_specs(self, *specs) -> 'HookSpec':
        """
        Merge multiple specs (classes) into a single instance of HookSpec.
        """

        dct = collections.OrderedDict()
        for s in specs:
            for hook_name, hook in s.hooks.items():
                assert hook_name not in dct
                dct[hook_name] = hook

        return type(
            '+'.join(str(s.__name__) for s in specs),
            (HookSpec,),
            dct,
        )()
