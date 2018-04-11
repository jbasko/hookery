import pytest

from hookery import Hook, Hookable, InstanceHook


@pytest.mark.parametrize('hook', [
    Hook(),
    Hook(single_handler=True),
])
def test_hook_handler_cannot_trigger_the_hook(hook):
    def handler():
        hook.trigger()

    hook(handler)

    with pytest.raises(RuntimeError) as exc_info:
        hook.trigger()

    assert 'cannot be triggered' in str(exc_info.value)


def test_multiple_instances_can_trigger_independently():
    class Base(Hookable):
        before = InstanceHook()

    b1 = Base()
    b2 = Base()

    @b2.before
    def handle_b2():
        return 'b2'

    @b1.before
    def handle_b1():
        return b2.before.trigger()

    assert b1.before.trigger() == [['b2']]


@pytest.mark.parametrize('hook', [
    Hook(),
    Hook(single_handler=True),
])
def test_exception_in_handler_resets_triggering_context(hook):
    def handler():
        raise ValueError()

    hook(handler)

    with pytest.raises(ValueError):
        hook.trigger()

    assert not hook._is_triggering
