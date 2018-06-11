import pytest

from hookery.v4 import Hook, HookSpec


class MyHooks(HookSpec):
    before = Hook()


def test_hook_handler_cannot_trigger_the_hook():
    my_hooks = MyHooks()

    @my_hooks.before
    def circular_handler():
        my_hooks.before.trigger()

    with pytest.raises(RuntimeError) as exc_info:
        my_hooks.before.trigger()

    assert 'cannot be triggered' in str(exc_info.value)


def test_exception_in_handler_resets_triggering_context():
    my_hooks = MyHooks()

    @my_hooks.before
    def failing_handler():
        raise ValueError()

    with pytest.raises(ValueError):
        my_hooks.before.trigger()

    assert not my_hooks.before._is_triggering
