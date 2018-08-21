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


def test_instance_hook_in_simple_class_with_two_class_hook_handlers(calls):
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
    assert c.h3.class_hook is C.h3

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


def test_derived_class_with_handlers_for_parent_hook(calls):
    class C:
        h4 = Hook()

        @h4
        def h4_handler_in_c(self):
            calls.register("h4_handler_in_c", self)
            return self

    class D(C):
        @C.h4
        def h4_handler_in_d(self):
            calls.register("h4_handler_in_d", self)
            return self

    # Make sure derived class's hook is bound to itself, not to parent
    assert C.h4 is not D.h4

    # Make sure D.h4 knows that it originates in the C class
    assert D.h4.base_hook._owner is C

    # Make sure handler decorated with @C.h4 does not end up as a handler of C.h4
    assert hooks.get_handlers(C.h4) == [C.h4_handler_in_c]

    # Make sure handler decorated with @C.h4 is registered as a subclass handler in C.h4
    assert C.h4._subclass_handlers == [D.h4_handler_in_d]

    # Lookup helpers
    assert hooks.get_hooks(D) == [D.h4]
    assert hooks.get_handlers(D.h4) == [C.h4_handler_in_c, D.h4_handler_in_d]

    # Instance
    d = D()
    assert hooks.get_hooks(d) == [d.h4]
    assert len(hooks.get_handlers(d.h4)) == 2

    # More depth

    class E(D):
        pass

    class F(E, D):
        pass

    assert hooks.get_handlers(E.h4) == [C.h4_handler_in_c, D.h4_handler_in_d]
    assert hooks.get_handlers(F.h4) == [C.h4_handler_in_c, D.h4_handler_in_d]

    # Trigger!
    f = F()
    assert len(hooks.get_handlers(f.h4)) == 2

    hooks.trigger(f.h4)
    assert len(calls) == 2
    assert calls[0].matches("h4_handler_in_c", f)
    assert calls[1].matches("h4_handler_in_d", f)


def test_instance_hook_with_class_and_instance_hook_handlers(calls):
    class C:
        h5 = Hook()

        @h5
        def h5_handler_in_c(self):
            calls.register("h5_handler_in_c", self)

    c = C()

    @c.h5
    def h5_handler_individually(cc):
        calls.register("h5_handler_individually", cc)

    assert len(hooks.get_handlers(c.h5)) == 2

    # Trigger!
    hooks.trigger(c.h5)
    assert len(calls) == 2
    assert calls[0].matches("h5_handler_in_c", c)
    assert calls[1].matches("h5_handler_individually", c)
