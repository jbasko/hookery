import pytest

from hookery import InstanceHook, hookable


def test_standalone_initialisation():
    before = InstanceHook('before')
    assert isinstance(before, InstanceHook)
    assert before.name == 'before'


def test_in_class_initialisation():
    @hookable
    class C:
        before = InstanceHook('before')

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
        before = InstanceHook('before')

    with pytest.raises(TypeError):
        C.before.trigger()


def test_can_be_triggered_via_instance():
    @hookable
    class C:
        before = InstanceHook('before')

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
