from hookery.v4 import BoundHook, Hook, HookSpec


class MyHookSpec(HookSpec):
    # Two ways to declare a hook -- as a method or as a descriptor directly.
    # If as a method then IDE won't be able to tell that it is replaced by a descriptor.
    # Also less intuitive. So we go with descriptor approach.
    event1 = Hook('event1')

    event2 = Hook('event2')


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
assert isinstance(my_hooks.event1, BoundHook)
assert my_hooks.event1.name == 'event1'


class Extended(Mixin, Base):
    @my_hooks
    def event1(self):
        return 'Extended'

    @my_hooks.event1
    def another_handler(self):
        return 'Another {}'.format(self)


@my_hooks.event1
def external_handler():
    return 'External'


ex = Extended()
print(my_hooks.event1.trigger(ex))

ey = Extended()
print(my_hooks.event1.trigger(ey))

print(my_hooks.event1.trigger(ex))

print(ex.another_handler())

print('-------------')


# TODO Use two hook specs in parallel?

class MySpec1(HookSpec):
    before = Hook()


class MySpec2(HookSpec):
    after = Hook()


all_hooks = HookSpec.merge_specs(MySpec1, MySpec2)
assert all_hooks.before
assert all_hooks.after


class MyClass:
    @all_hooks
    def before(self):
        print('doing before')

    @all_hooks.after
    def do_after(self):
        print('doing after')


c = MyClass()
d = MyClass()

all_hooks.before.trigger(c)
all_hooks.after.trigger(c)
