import pytest

from hookery.v4 import BoundHook, GlobalContext, Hook, HookSpec


class MyHooks(HookSpec):
    before = Hook()


class Base:
    pass


class Extended(Base):
    pass


def test_hook_becomes_a_bound_hook_for_instance():
    my_hooks = MyHooks()

    assert isinstance(MyHooks.before, Hook)
    assert MyHooks.before.name == 'before'

    assert isinstance(my_hooks.before, BoundHook)
    assert my_hooks.before.name == 'before'

    assert my_hooks.before.spec is my_hooks


@pytest.mark.parametrize('ctx', [
    object,
    object(),
    Base,
    Base(),
    Extended,
    Extended(),
])
def test_calling_bound_hook_creates_handler_registration_method(ctx):
    my_hooks = MyHooks()

    register_handler = my_hooks.before(ctx)

    assert callable(register_handler)
    assert register_handler.hook_name == 'before'
    assert register_handler.ctx is ctx

    @register_handler
    def handler():
        return {'ctx': ctx}

    assert len(my_hooks.before.get_handlers(ctx)) == 1

    # Calling with a different context should not return the handler registered above
    assert len(my_hooks.before.get_handlers(object())) == 0


def test_calling_bound_hook_with_no_ctx_creates_global_handler_registration_method():
    my_hooks = MyHooks()

    register_handler = my_hooks.before()

    assert callable(register_handler)
    assert register_handler.hook_name == 'before'
    assert register_handler.ctx is GlobalContext

    @register_handler
    def handler():
        return {'ctx': GlobalContext}

    assert len(my_hooks.before.get_handlers()) == 1

    # This handler is called for all contexts because it is global
    assert len(my_hooks.before.get_handlers(object)) == 1
    assert len(my_hooks.before.get_handlers(object())) == 1


def test_hook_get_handlers_returns_handlers():
    my_hooks = MyHooks()

    assert my_hooks.before.get_handlers() == []

    class MyClass:
        @my_hooks
        def before(self):
            return '{}.before'.format(self)

    assert my_hooks.before.get_handlers() == []
    assert len(my_hooks.before.get_handlers(MyClass)) == 0
    assert len(my_hooks.before.get_handlers(MyClass())) == 1


def test_global_context_handler_registered_and_called():
    my_hooks = MyHooks()

    @my_hooks.before  # NB! No parentheses here. Registers a handler with ctx=GlobalContext
    def global_handler():
        return 'global1'

    @my_hooks.before()  # NB! Parentheses here. Creates a register_handler with ctx=GlobalContext
    def global_handler2():
        return 'global2'

    assert len(my_hooks.before.get_handlers()) == 2
    assert len(my_hooks.before.get_handlers(object)) == 2
    assert len(my_hooks.before.get_handlers(object())) == 2

    assert my_hooks.before.trigger() == ['global1', 'global2']
    assert my_hooks.before.trigger(object) == ['global1', 'global2']
    assert my_hooks.before.trigger(object()) == ['global1', 'global2']
    assert my_hooks.before.trigger(Extended) == ['global1', 'global2']
    assert my_hooks.before.trigger(Extended()) == ['global1', 'global2']


def test_merged_hook_specs():
    class MySpec1(HookSpec):
        before = Hook()

    class MySpec2(HookSpec):
        after = Hook()

    all_hooks = HookSpec.merge_specs(MySpec1, MySpec2)

    assert isinstance(all_hooks.before, BoundHook)
    assert isinstance(all_hooks.after, BoundHook)

    @all_hooks.before
    def before():
        return 'global.before'

    @all_hooks.after
    def handle_after():
        return 'global.after'

    assert len(all_hooks.before.get_handlers()) == 1
    assert len(all_hooks.after.get_handlers()) == 1

    assert all_hooks.before.trigger() == ['global.before']
    assert all_hooks.after.trigger() == ['global.after']


def test_mixin_two_hook_specs():
    class MySpec1(HookSpec):
        before = Hook()

    class MySpec2(HookSpec):
        after = Hook()

    class MySpec(MySpec1, MySpec2):
        pass

    all_hooks = MySpec()
    assert isinstance(all_hooks.before, BoundHook)
    assert isinstance(all_hooks.after, BoundHook)

    @all_hooks.before
    def before():
        return 'global.before'

    @all_hooks.after
    def handle_after():
        return 'global.after'

    assert len(all_hooks.before.get_handlers()) == 1
    assert len(all_hooks.after.get_handlers()) == 1

    assert all_hooks.before.trigger() == ['global.before']
    assert all_hooks.after.trigger() == ['global.after']
