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


"""
import collections
from typing import Callable, Type


class Hook:
    def __init__(self, name: str, spec: Type['HookSpec']):
        self.name = name
        self.spec = spec

    def __call__(self, f):
        """
        Decorator for handlers of this hook.
        The handler being decorated doesn't have to be carry the hook's name.
        """
        self.spec.register_handler(self, f)


class HookSpec:
    _handlers = collections.defaultdict(list)

    @classmethod
    def hook(cls, f) -> Hook:
        """
        Decorator for a hook declaration in a HookSpec class.
        """
        hook_name = f.__name__

        # TODO Maybe should return a descriptor! because we need to have spec instance, not class!

        return Hook(hook_name, spec=cls)

    @classmethod
    def register_handler(cls, hook: Hook, handler: Callable):
        cls._handlers[hook.name].append(handler)


class MyHookSpec(HookSpec):
    @HookSpec.hook
    def event1(self):
        pass

    def __call__(self, f):
        """
        Decorator for functions and methods whose name tells which hook they are handling.
        """
        hook_name = f.__name__
        assert hasattr(self, hook_name)


my_hooks = MyHookSpec()


class Base:
    @my_hooks
    def event1(self):
        return 'Base'


class Mixin:
    @my_hooks
    def event1(self):
        return 'Mixin'


class Extended(Mixin, Base):
    @my_hooks
    def event1(self):
        return 'Extended'

    @my_hooks.event1
    def another_handler(self):
        return 'Another'


@my_hooks.event1
def external_handler():
    return 'External'


print(my_hooks.__dict__)
print(MyHookSpec.__dict__)


# e = Extended()
# print(Extended.__dict__)
# print(e.__dict__)
# e.event1()
