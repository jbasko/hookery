# hookery, version 4

## Example 1

We're developing a framework to allow us compose a command-line interface by combining features of
multiple individual command-line interfaces.

Here's the specification of the interface :

    class CliHooks(HookSpec):
        init_parser = Hook()
        inject_args = Hook()
        get_plugins = Hook()



A hook is a instance method that needs to be called in all classes of the instance's class tree.

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

The goal is to invoke ``e.event1`` in a way that all implementations of ``event1`` get called with ``e`` passed as ``self``.

If you call ``e.event1()`` after interpreting the code above, you will get ``Extended``, but what we want is
to get a list of results collected from all hook handlers: ``['Mixin', 'Base', 'Extended']``

Implementation Proposal:

The implementation must alert any reader of the handler code that these are special methods and do not
override parent class methods, and should not therefore call ``super()``.
A decorator is a good way to alert user and also to point to the declaration of the hook that is
being handled:

    class Extended(Mixin, Base):
        @my_hooks
        def event1(self):
            return 'Extended'

Now, ``my_hooks`` could be an individual hook, but this becomes more flexible if ``my_hooks`` is actually
an object describing a set of hooks -- a hook specification. This information could then be used to
validate the hook handler on registration.

    class MyHookSpec:
        def event1(self):
            pass

    my_hooks = MyHookSpec()

If user sees a method in one of the derived classes, for example, ``Extended.event1``, they will intuitively
assume that this method overrides ``Base.event1`` (unless they check the source of Base).

Now, ``my_hooks.event1`` could also become a decorator to register a handler for cases when the name of
the method being decorated doesn't match hook name ``event1``:

    class Extended(Mixin, Base):
        @my_hooks
        def event1(self):
            return 'Extended'

        @my_hooks.event1
        def another_handler(self):
            return 'Another'

``event1`` handlers don't have to be instance methods -- they could also be
functions:

    @my_hooks.event1
    def external_handler():
        return 'External Handler'

We don't replace the functions declared in classes.
We just register them as handlers.
Hooks should be triggered with BoundHook.trigger() method.

Handlers are registered in the hook spec against classes.
Because you are registering against hook spec, there cannot be any instance-specific handlers.
