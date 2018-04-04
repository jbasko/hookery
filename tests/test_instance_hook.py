import pytest

from hookery import InstanceHook, hookable


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


def test_strict_args():
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
