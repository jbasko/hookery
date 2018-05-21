import inspect

import pytest

from hookery import ClassHook, Hook, InstanceHook, hookable


@pytest.mark.parametrize('hook_cls', [Hook, ClassHook, InstanceHook])
def test_hook_is_falsey_if_it_has_no_handlers(hook_cls):
    h1 = hook_cls('h1')
    assert not h1

    h1(lambda: None)
    assert h1


def test_hook_can_be_overwritten_by_another_hook():
    @hookable
    class B:
        before = InstanceHook()

    B.before(lambda: 'B.before')

    class C(B):
        before = InstanceHook()  # overwrite, has no connection B.before

    assert C.before.parent_class_hook is None

    C.before(lambda: 'C.before')

    c = C()
    c.before(lambda: 'c.before')

    assert isinstance(c.before, InstanceHook)
    assert c.before.is_instance_associated

    assert c.before.trigger() == ['C.before', 'c.before']

    class D(C):
        pass

    assert D.before.parent_class_hook is C.before


def test_hook_in_same_class_where_it_is_declared():
    @hookable
    class B:
        before = InstanceHook()
        after = ClassHook()

        @before
        def on_before(self, x):
            assert isinstance(self, B)
            return x * 3

        @after
        def on_after(cls, y):
            assert cls is B
            return y * 5

    assert len(B.before.handlers) == 1

    assert B().before
    assert B.after

    assert B().before.trigger(x=20, y=10) == [60]
    assert B.after.trigger(x=20, y=10) == [50]

    # In a derived class the logic is different so must test that too:

    class C(B):
        between = InstanceHook()
        betwixt = ClassHook()

        @between
        def on_between(self, x):
            assert isinstance(self, C)
            return x * 4

        @betwixt
        def on_betwixt(cls, y):
            assert cls is C
            return y * 6

    assert C().between
    assert C.betwixt

    # c00 = C()
    # assert c00.between.subject is c00

    assert C().between.trigger(x=20, y=10) == [80]
    assert C.betwixt.trigger(x=20, y=10) == [60]


def test_hook_with_consume_generators_false():
    hook = Hook(consume_generators=False)

    @hook
    def generate_things():
        yield from range(10)

    @hook
    def generate_other_things():
        yield from range(5)

    results = hook.trigger()
    assert isinstance(results, list)
    assert inspect.isgenerator(results[0])
    assert inspect.isgenerator(results[1])
    assert list(results[0]) == list(range(10))
    assert list(results[1]) == list(range(5))
