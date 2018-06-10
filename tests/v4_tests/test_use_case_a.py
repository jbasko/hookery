"""
Use Case A:

A hook is an instance method that needs to be called in all classes of the instance's class tree.

    class Base:
        def event1(self):
            return 'Base'

    class Mixin:
        def event1(self):
            return 'Mixin'

    class Extended(Mixin, Base):
        def event1(self):
            return 'Extended'

    e = Extended()

The goal is to invoke `e.event1` in a way that all implementations of `event1` get called with `e` passed as `self`.

If you call `e.event1()` after interpreting the code above, you will get `Extended`, but what we want is
to get a list of results collected from all hook handlers: `['Mixin', 'Base', 'Extended']`

Implementation Proposal:

The implementation must alert any reader of the handler code that these are special methods and do not
override parent class methods, and should not therefore call `super()`.
A decorator is a good way to alert user and also to point to the declaration of the hook that is
being handled:

    class Extended(Mixin, Base):
        @my_hooks
        def event1(self):
            return 'Extended'

Now, `my_hooks` could be an individual hook, but this becomes more flexible if `my_hooks` is actually
an object describing a set of hooks -- a hook specification. This information could then be used to
validate the hook handler on registration.

    class MyHookSpec:
        def event1(self):
            pass

    my_hooks = MyHookSpec()

If user sees a method in one of the derived classes, for example, `Extended.event1`, they will intuitively
assume that this method overrides `Base.event1` (unless they check the source of Base).

Now, `my_hooks.event1` could also become a decorator to register a handler for cases when the name of
the method being decorated doesn't match hook name `event1`:

    class Extended(Mixin, Base):
        @my_hooks
        def event1(self):
            return 'Extended'

        @my_hooks.event1
        def another_handler(self):
            return 'Another'

`event1` handlers don't have to be instance methods -- they could also be
functions:

    @my_hooks.event1
    def external_handler():
        return 'External Handler'

Questions:

    1. Should we replace e.event1 with the new handler that takes all of the above into consideration,
       or should we instead use something like e.event1.trigger() ?

Issues:

    Where do we register the handlers?

    Class based handlers?
    Instance based handlers?

What are the hooks for? To change the instance or to have external, unrelated side-effects?

Handlers are registered in the hook spec against classes.
Because you are registering against hook spec, there cannot be any instance-specific handlers.
How do you then have instance-specific handlers?
Maybe instance.hook_name.register_handler()?
Because instance.hook_name is different from class.hook_name.
It's a descriptor. Should be one.

"""
import collections
from typing import Type, Union


class HookDescriptor:
    def __init__(self, name: str):
        self.name = name

    @property
    def _attr_name(self):
        return 'hook#{}'.format(self.name)

    def __get__(self, instance, owner) -> Union['Hook', 'HookDescriptor']:
        if instance is None:
            return self
        else:
            if not hasattr(instance, self._attr_name):
                setattr(instance, self._attr_name, Hook(self.name, spec=instance))
            return getattr(instance, self._attr_name)

    def __set_name__(self, owner, name):  # Python 3.6
        owner.name = name

    def __repr__(self):
        return '<{} {!r}>'.format(
            self.__class__.__name__,
            self.name
        )


class Hook:
    def __init__(self, name: str, spec: 'HookSpec'):
        self.name = name
        self.spec = spec  # type: HookSpec

    def __call__(self, f):
        """
        Decorator to register handlers for this hook.
        The handler being decorated doesn't have to carry the hook's name.
        """
        self.spec._register_handler(self.name, f)
        return self.spec._get_trigger(self.name)


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
            if isinstance(v, HookDescriptor):
                # Hook declared as a descriptor
                if v.name is None:
                    # Set name for a hook declared as a nameless descriptor
                    v.name = k

                clean_dct[k] = v
                clean_dct['hooks'][k] = v

            elif callable(v) and not k.startswith('_'):
                # Hook declared as a method, must replace with a descriptor
                hook_descr = HookDescriptor(k)
                clean_dct[k] = hook_descr
                clean_dct['hooks'][k] = hook_descr

            else:
                # Normal attribute
                clean_dct[k] = v

        return super().__new__(meta, name, bases, clean_dct)


class HookSpec(metaclass=HookSpecMeta):
    """
    All methods of HookSpec whose name does not start with "_" are hooks.
    """
    def __init__(self):
        self._handlers = collections.defaultdict(list)
        self._triggers = {}

    def _register_handler(self, hook_name, handler):
        assert hook_name in self.hooks
        self._handlers[hook_name].append(handler)

    def _get_trigger(self, hook_name):
        if hook_name not in self._triggers:
            def trigger(*args, **kwargs):
                results = [h(*args, **kwargs) for h in self._handlers[hook_name]]
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
        return self._get_trigger(hook_name)


class MyHookSpec(HookSpec):
    # Two ways to declare a hook -- as a method or as a descriptor directly.
    # If as a method then IDE won't be able to tell that it is replaced by a descriptor.
    # Also less intuitive. So we go with descriptor approach.
    event1 = HookDescriptor('event1')

    event2 = HookDescriptor('event2')


my_hooks = MyHookSpec()
assert list(my_hooks.hooks) == ['event1', 'event2']


class Base:
    @my_hooks
    def event1(self):
        return 'Base({})'.format(self)


class Mixin:
    @my_hooks
    def event1(self):
        return 'Mixin({})'.format(self)


assert callable(my_hooks.event1)
assert isinstance(my_hooks.event1, Hook)
assert my_hooks.event1.name == 'event1'


class Extended(Mixin, Base):
    @my_hooks
    def event1(self):
        return 'Extended'

    @my_hooks.event1
    def another_handler(self):
        return 'Another {}'.format(self)


# @my_hooks.event1
# def external_handler():
#     return 'External'


ex = Extended()
print(ex.event1())

ey = Extended()
print(ey.event1())

print(ex.event1())

print(ex.another_handler())

