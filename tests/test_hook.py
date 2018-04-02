import pytest

from hookery import ClassHook, GlobalHook, InstanceHook, hookable


@pytest.mark.parametrize('hook_cls', [GlobalHook, ClassHook, InstanceHook])
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
