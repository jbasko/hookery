import pytest

from hookery import GlobalHook, Hook, hookable


def test_initialisation():
    before = GlobalHook('before')
    assert isinstance(before, Hook)
    assert before.name == 'before'
    assert before.subject is not None


def test_cannot_initialise_without_name():
    with pytest.raises(ValueError):
        GlobalHook()


def test_hookable_does_not_modify_global_hooks():
    @hookable
    class C:
        before = GlobalHook('global_before')

    assert isinstance(C.before, GlobalHook)
    assert C.before.subject is not C
    assert C.before.name == 'global_before'

    assert C.before.trigger() == []

    C.before(lambda: 123)
    assert C.before.trigger() == [123]


def test_single_handler_hook():
    before = GlobalHook('before', single_handler=True)
    assert before.single_handler

    before(lambda: 1)
    assert before.trigger() == 1

    before(lambda: 2)
    assert before.trigger() == 2


def test_trigger_only_accepts_kwargs():
    before = GlobalHook('before')

    before.trigger(a=1)
    before.trigger(a=1, b=2)

    with pytest.raises(TypeError):
        before.trigger(1, 2)

    with pytest.raises(TypeError):
        before.trigger(1)

    with pytest.raises(TypeError):
        before.trigger(None)
