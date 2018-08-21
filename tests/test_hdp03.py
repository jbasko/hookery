from hookery.hdps.hdp03 import Hook, hooks, ClassHook, InstanceHook


def test_class_hook_in_simple_class_with_no_handlers():
    class C:
        h1 = Hook()

    # The base hook
    assert isinstance(C.h1.base_hook, Hook)
    assert C.h1.base_hook.name == "h1"
    assert C.h1.base_hook._unbound_handlers == []

    # The hook itself
    assert C.h1.name == "h1"
    assert isinstance(C.h1, ClassHook)
    assert not isinstance(C.h1, Hook)

    # Lookup helpers
    assert hooks.get_hooks(C) == [C.h1]
    assert hooks.get_handlers(C.h1) == []


def test_class_hook_in_simple_class_with_two_handlers():
    class C:
        h2 = Hook()

        @h2
        def h2_handler_1(self):
            return self

        @h2
        def h2_handler_2(self):
            return self

    # Ensure the handlers are intact
    obj = object()
    assert callable(C.h2_handler_1)
    assert C.h2_handler_1(obj) is obj
    assert callable(C.h2_handler_2)
    assert C.h2_handler_2(obj) is obj

    # The base hook
    assert C.h2.base_hook.name == "h2"
    assert len(C.h2.base_hook._unbound_handlers) == 2
    assert C.h2.base_hook._unbound_handlers[0].__name__ == 'h2_handler_1'
    assert C.h2.base_hook._unbound_handlers[1].__name__ == 'h2_handler_2'

    # Lookup helpers
    assert hooks.get_hooks(C) == [C.h2]
    assert len(hooks.get_handlers(C.h2)) == 2


def test_instance_hook_in_simple_class_with_two_handlers(calls):
    class C:
        h3 = Hook()

        @h3
        def h3_handler_1(self):
            calls.register("h3_handler_1", self)
            return self

        @h3
        def h3_handler_2(self):
            calls.register("h3_handler_2", self)
            return self

    c = C()

    assert isinstance(c.h3, InstanceHook)
    assert c.h3.name == "h3"

    assert isinstance(c.h3.base_hook, Hook)

    # Lookup helpers
    assert hooks.get_hooks(c) == [c.h3]
    assert len(hooks.get_handlers(c.h3)) == 2

    # Make sure the handlers are bound correctly
    for handler in hooks.get_handlers(c.h3):
        assert handler() is c

    # Trigger
    calls.clear()
    hooks.trigger(c.h3)

    assert len(calls) == 2
    assert calls[0].matches("h3_handler_1", c)
    assert calls[1].matches("h3_handler_2", c)
