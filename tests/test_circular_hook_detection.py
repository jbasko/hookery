import pytest

from hookery import Hook


@pytest.mark.parametrize('hook', [
    Hook(),
    Hook(single_handler=True),
])
def test_hook_handler_cannot_trigger_the_hook(hook):
    hook = Hook()

    def handler():
        hook.trigger()

    hook(handler)

    with pytest.raises(RuntimeError) as exc_info:
        hook.trigger()

    assert 'cannot be triggered' in str(exc_info.value)
