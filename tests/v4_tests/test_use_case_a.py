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

"""