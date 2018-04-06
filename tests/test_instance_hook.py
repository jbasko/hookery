import functools

import pytest

from hookery import Hookable, InstanceHook, hookable


def test_standalone_initialisation():
    before = InstanceHook('before')
    assert isinstance(before, InstanceHook)
    assert before.name == 'before'


def test_in_class_initialisation():
    @hookable
    class C:
        before = InstanceHook()

    assert isinstance(C.before, InstanceHook)
    assert C.before.subject is C
    assert C.before.name == 'before'

    c = C()
    assert c.before.name == 'before'
    assert isinstance(c.before, InstanceHook)
    assert c.before.subject is c

    assert c.before is not C.before


def test_cannot_be_triggered_via_class():
    @hookable
    class C:
        before = InstanceHook()

    with pytest.raises(TypeError):
        C.before.trigger()


def test_can_be_triggered_via_instance():
    @hookable
    class C:
        before = InstanceHook()

    assert C().before.trigger() == []


def test_inheritance():
    @hookable
    class Base:
        before = InstanceHook()

    Base.before(lambda: 'Base.before')

    @hookable
    class Derived(Base):
        after = InstanceHook()

    Derived.before(lambda: 'Derived.before')

    class Deep(Derived):
        pass

    Deep.before(lambda: 'Deep.before')

    e1 = Deep()
    e1.before(lambda: 'e1.before')

    e2 = Deep()
    e2.before(lambda: 'e2.before')

    class Other(Derived):
        pass

    Other.before(lambda: 'other.before')

    assert e1.before.trigger() == ['Base.before', 'Derived.before', 'Deep.before', 'e1.before']
    assert e2.before.trigger() == ['Base.before', 'Derived.before', 'Deep.before', 'e2.before']


def test_trigger_only_accepts_kwargs():
    @hookable
    class C:
        before = InstanceHook()

    C().before.trigger(a=1)
    C().before.trigger(a=1, b=2)

    with pytest.raises(TypeError):
        C().before.trigger(1, 2)

    with pytest.raises(TypeError):
        C().before.trigger(1)

    with pytest.raises(TypeError):
        C().before.trigger(None)


def test_self_is_populated_for_instance_hook():
    @hookable
    class C:
        before = InstanceHook()

    class D(C):
        @C.before
        def on_before(self, x):
            assert isinstance(self, D)
            return x * 3

    d = D()
    assert d.before.trigger(x=5) == [15]


def test_strict_args_on_handler_registration():
    @hookable
    class C:
        before = InstanceHook(args=['x', 'y'])

    assert C.before.args == ('x', 'y')
    assert C().before.args == ('x', 'y')

    C.before(lambda: None)
    C.before(lambda self: None)
    C.before(lambda self, x: None)
    C.before(lambda self, x, y: None)
    C.before(lambda x, y: None)

    with pytest.raises(RuntimeError):
        C.before(lambda a: None)

    with pytest.raises(RuntimeError):
        C.before(lambda self, b: None)


def test_raise_value_error_if_trigger_receives_unknown_args():
    @hookable
    class C:
        before = InstanceHook(args=['x', 'y'])

    c = C()
    c.before.trigger(x=1, y=2)

    with pytest.raises(ValueError):
        c.before.trigger(a=1)

    with pytest.raises(ValueError):
        c.before.trigger(x=1, a=2)

    with pytest.raises(ValueError):
        c.before.trigger(x=1, y=2, a=2)

    # Allow underscore prefixed unknown kwargs
    c.before.trigger(x=1, y=2, _something_unbelievable=True)


def test_can_stack_hook_handlers_in_subclass():
    @hookable
    class B:
        before = InstanceHook()
        after = InstanceHook()

    class C(B):
        @B.before
        @B.after
        def greeting(self):
            return 'Hello {}'.format(self.__class__.__name__)

    assert C().before.trigger() == ['Hello C']
    assert C().after.trigger() == ['Hello C']


def test_can_stack_hook_handlers_in_same_class():
    @hookable
    class B:
        before = InstanceHook()
        after = InstanceHook()

        @after
        @before
        def greeting(self, name):
            return 'Hello {}'.format(name)

    b = B()
    assert b.before.trigger(name='X') == ['Hello X']
    assert b.after.trigger(name='Y') == ['Hello Y']


def test_can_register_partials_and_functions_with_kwargs_with_defaults_as_handlers():
    @hookable
    class B:
        before = InstanceHook()

    def multiply(a, b):
        return a * b

    B.before(functools.partial(multiply, a=2, b=3))
    assert B().before.trigger() == [2 * 3]
    assert B().before.trigger(a=5) == [3 * 5]
    assert B().before.trigger(b=7) == [2 * 7]

    B.before(functools.partial(functools.partial(multiply, b=11), a=13))
    assert B().before.trigger() == [2 * 3, 11 * 13]
    assert B().before.trigger(a=17) == [17 * 3, 17 * 11]
    assert B().before.trigger(b=23) == [2 * 23, 13 * 23]

    B.before(lambda a=99, b=101: a * b)
    assert B().before.trigger() == [2 * 3, 13 * 11, 99 * 101]
    assert B().before.trigger(b=103) == [2 * 103, 13 * 103, 99 * 103]


def test_can_pass_self_to_handler():
    class B(Hookable):
        before = InstanceHook()

        @before
        def on_before1(self):
            assert isinstance(self, B)
            return 1

    @B.before
    def on_before2(self):
        assert isinstance(self, B)

    b = B()
    b.before.trigger()
    b.before.trigger(self=b)
