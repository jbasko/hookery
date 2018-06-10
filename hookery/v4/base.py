import collections
from typing import Union

from hookery.utils import optional_args_func


class Hook:
    """
    Represents an unbound hook.
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

    def __set_name__(self, owner, name):  # Python 3.6
        owner.name = name

    def __repr__(self):
        return '<{} {!r}>'.format(
            self.__class__.__name__,
            self.name
        )

    @property
    def _attr_name(self):
        return 'hook#{}'.format(self.name)

    def trigger(self, *args, **kwargs):
        """
        Unbound Hook instances should not be triggered.
        This is just to help with debugging.
        """
        raise RuntimeError('{} instance should not be triggered'.format(self.__class__))


class BoundHook:
    """
    A hook that is bound to an instance of hook specification.
    """
    def __init__(self, name: str, spec: 'HookSpec'):
        self.name = name
        self.spec = spec  # type: HookSpec

    def __call__(self, f):
        """
        Decorator to register handlers for this hook.
        The handler being decorated doesn't have to carry the hook's name.
        """
        self.spec._register_handler(self.name, f)
        return f

    def trigger(self, ctx, *args, **kwargs):
        """
        `ctx` is the object on which the event is happening; it is used to
        determine the class whose handlers should be invoked. It is also
        passed as the first positional argument to the handlers which
        for class based handlers is usually self.
        """
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
        self._handlers = collections.defaultdict(list)
        self._triggers = {}

    def _register_handler(self, hook_name, handler):
        if hook_name not in self.hooks:
            raise ValueError('Unknown hook {!r}'.format(hook_name))

        # Mark the handler so we can distinguish it from hook-named methods that aren't registered.
        add_to_handler_marker(handler, hook_name)

        print(get_handler_marker(handler))
        assert handles_hook(handler, hook_name)

        # TODO Is this even needed now?
        self._handlers[hook_name].append(optional_args_func(handler))

    def _get_handlers(self, hook_name, ctx):
        handlers = []

        for base in reversed(type(ctx).__mro__[:-1]):
            if hook_name in base.__dict__:
                handler = base.__dict__[hook_name]
                if handles_hook(handler, hook_name):
                    handlers.append(handler)

        return handlers

    def _get_trigger(self, hook_name, ctx):
        if hook_name not in self._triggers:
            def trigger(*args, **kwargs):
                results = [h(*args, **kwargs) for h in self._get_handlers(hook_name, ctx)]
                return results
            self._triggers[hook_name] = trigger
        return self._triggers[hook_name]

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
