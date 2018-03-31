import pytest

from hookery import ClassHook, GlobalHook, InstanceHook


@pytest.mark.parametrize('hook_cls', [GlobalHook, ClassHook, InstanceHook])
def test_hook_is_falsey_if_it_has_no_handlers(hook_cls):
    h1 = hook_cls('h1')
    assert not h1

    h1(lambda: None)
    assert h1
