from hookery.v4 import HookSpec, Hook


class MyHooks(HookSpec):
    before = Hook()
    after = Hook()


def test_hook_spec_hook_attr_is_register_handler_method_factory():
    my_hooks = MyHooks()
    assert callable(my_hooks.before)

    obj1 = object()
    obj2 = object()

    register_handler = my_hooks.before(obj1)
    assert callable(register_handler)

    dummy_handler = lambda self: None
    register_handler(dummy_handler)

    assert my_hooks._get_handlers('before', obj2) == []
    assert my_hooks._get_handlers('before', obj1) == [dummy_handler]


def test_hook_get_handlers_returns_handlers():
    my_hooks = MyHooks()

    assert my_hooks.before.get_handlers() == []
    assert my_hooks.after.get_handlers() == []

    class MyClass:
        @my_hooks
        def before(self):
            return '{}.before'.format(self)

    assert my_hooks.before.get_handlers() == []
    assert len(my_hooks.before.get_handlers(MyClass)) == 0
    assert len(my_hooks.before.get_handlers(MyClass())) == 1
