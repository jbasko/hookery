import abc
import collections
import contextlib
import types
from typing import Any, Callable, Union

from hookery.utils import optional_args_func


class _GlobalContext:
    """
    A special object marking global context.
    """

    def __repr__(self):
        return '<GlobalContext{}>'.format(id(self))


GlobalContext = _GlobalContext()


class _ImplicitClassContext:
    def __repr__(self):
        return '<ImplicitClassContext{}>'.format(id(self))


ImplicitClassContext = _ImplicitClassContext()


class Hook:
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

    def trigger(self, ctx=None, *args, **kwargs):
        raise RuntimeError('{} instance should not be triggered'.format(self.__class__))

    def __call__(self, ctx_or_func=None, *args, **kwargs):
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


class BoundHook:
    """
    A hook that is bound to an instance of hook specification (:class:`HookSpec`).

    See :class:`Hook`.
    """
    def __init__(self, name: str, spec: 'HookSpec'):
        self.name = name
        self.spec = spec  # type: HookSpec
        self._is_triggering = False

    def __call__(self, ctx=GlobalContext, *args, **kwargs):
        """
        Creates a handler registration function against the ctx object --
        the returned function can be used to register a handler of this hook on the ctx object.

        If `ctx` appears to be a simple function this will register it as a handler
        in the global context.
        """

        if isinstance(ctx, types.FunctionType):
            self.spec.register_handler(self.name, ctx, ctx=GlobalContext)
            return ctx

        def register_handler(f):
            self.spec.register_handler(self.name, f, ctx=ctx)

        # For testing & debugging
        register_handler.hook_name = self.name
        register_handler.ctx = ctx

        return register_handler

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

    def trigger(self, ctx=GlobalContext, *args, **kwargs):
        """
        Trigger hook handlers registered against the specified context.
        """
        results = []
        for handler in self.get_handlers(ctx=ctx):
            with self._triggering_ctx():
                if ctx is not None and ctx is not GlobalContext:
                    results.append(handler(ctx, *args, **kwargs))
                else:
                    results.append(handler(*args, **kwargs))
        return results

    def get_handlers(self, ctx=GlobalContext):
        """
        Returns a list of handlers for this hook associated with the specified context.
        """
        return self.spec.get_handlers(self.name, ctx)


class HookSpecMeta(type):
    @classmethod
    def __prepare__(metacls, name, bases):
        # To preserve attribute declaration order in Python 3.5
        return collections.OrderedDict()

    def __new__(meta, name, bases, dct):
        """
        Hooks are declared as class variables of a HookSpec class.
        """

        clean_dct = collections.OrderedDict()
        clean_dct['hooks'] = collections.OrderedDict()

        for b in bases:
            # When inheriting from a HookSpec, must make sure that all hooks are inherited too.
            if HookSpec in b.__mro__[1:]:
                for k, v in b.hooks.items():
                    if k in dct:
                        # Ignore hooks from bases that are overridden in the class itself
                        continue
                    clean_dct['hooks'][k] = v

        for k, v in dct.items():
            if k == 'hooks':
                # Skip the placeholder in HookSpec base class.
                assert v is None
                continue

            if isinstance(v, Hook):
                # Hook declared as a descriptor
                if v.name is None:
                    # Set name for a hook declared as a nameless descriptor
                    # Only needed in Python 3.5
                    v.name = k

                clean_dct[k] = v
                clean_dct['hooks'][k] = v

            else:
                # Normal attribute
                clean_dct[k] = v

        return super().__new__(meta, name, bases, clean_dct)


def _get_handler_marker(handler):
    marker = getattr(handler, '_hookery_marker', None)
    if marker is None:
        marker = []
    return marker


def _set_handler_marker(handler, marker):
    setattr(handler, '_hookery_marker', marker)


def _add_to_handler_marker(handler, hook_name):
    marker = _get_handler_marker(handler)
    marker.append(hook_name)
    _set_handler_marker(handler, marker)


def _handles_hook(handler, hook_name):
    return hook_name in _get_handler_marker(handler)


class HookSpec(metaclass=HookSpecMeta):
    """
    :class:`HookSpec` class (and classes derived from it) serve as hook specifications.
    Instances of this class serve as hook handler registries for handlers without implicit context.
    """

    # Ordered dictionary of all bound hooks. Initialised in :class:`HookSpecMeta`
    hooks = None  # type: collections.OrderedDict

    def __init__(self):
        self._ctx_specific_handlers = collections.defaultdict(list)
        self._triggers_cache = {}

    def register_handler(self, hook_name: str, handler: Callable, ctx: Any=GlobalContext):
        """
        Register a handler of an event, and optionally specify context to which this handler applies.
        """
        if hook_name not in self.hooks:
            raise ValueError('Unknown hook {!r}'.format(hook_name))

        # Mark the handler so we can distinguish it from methods that just happen to have the same name,
        # but aren't marked as handlers.
        _add_to_handler_marker(handler, hook_name)

        assert _handles_hook(handler, hook_name)

        # We only store handlers that are associated with a ctx object.
        # `ImplicitClassContext` is a special context that should not be registered handlers for
        # because these handlers can be found by checking __dict__ of all base classes
        # in the hook context object's class hierarchy. See :meth:`HookSpec.get_handlers`.
        if ctx is not None and ctx is not ImplicitClassContext:
            self._ctx_specific_handlers[(ctx, hook_name)].append(optional_args_func(handler))

    def get_handlers(self, hook_name, ctx=GlobalContext):
        """
        Return a list of handlers associated with the named hook in the specified context.
        """

        # TODO Should cache handlers on the context object.

        handlers = []

        if ctx is not None and ctx is not GlobalContext:
            # Handlers associated with classes in the class tree of the context object
            for base in reversed(type(ctx).__mro__[:-1]):
                if hook_name in base.__dict__:
                    handler = base.__dict__[hook_name]
                    if _handles_hook(handler, hook_name):
                        handlers.append(handler)

            # Handlers associated with the individual context object
            handlers.extend(self._ctx_specific_handlers[(ctx, hook_name)])

        # Handlers associated with the GlobalContext
        handlers.extend(self._ctx_specific_handlers[(GlobalContext, hook_name)])

        return handlers

    def __call__(self, f):
        """
        Decorator for methods whose name tells which hook they are handling.
        The decorated function itself is returned.
        """
        hook_name = f.__name__

        # Register the handler against the special context which effectively
        # means the handler is not actually registered in registry -- it will
        # be found at event trigger time based on the class hierarchy of the
        # class of the event context object.
        self.register_handler(hook_name, f, ctx=ImplicitClassContext)

        return f
