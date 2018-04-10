from hookery import BoundHandler, Handler, Hook, Hookable, InstanceHook


def test_bound_handler_for_simple_hook():
    hook = Hook()

    h1 = hook(lambda: 123)

    assert isinstance(h1, Handler)
    assert not isinstance(h1, BoundHandler)

    assert hook.handlers[0]() == 123
    assert isinstance(hook.handlers[0], BoundHandler)
    assert hook.handlers[0].hook is hook

    assert hook.trigger() == [123]


def test_bound_handler_for_instance_and_class_hooks():
    class Base(Hookable):
        before = InstanceHook()

        before(lambda: 1)

    Base.before(lambda: 2)

    b = Base()
    b.before(lambda: 3)

    class_associated_handlers = Base.before.handlers
    assert isinstance(class_associated_handlers[0], BoundHandler)
    assert class_associated_handlers[0].hook is Base.before

    assert isinstance(class_associated_handlers[1], BoundHandler)
    assert class_associated_handlers[1].hook is Base.before

    instance_associated_handlers = b.before.handlers
    assert isinstance(instance_associated_handlers[0], BoundHandler)
    assert instance_associated_handlers[0].hook is b.before


def test_bound_handler_of_bound_handler():
    hook = Hook()
    handler = Handler(func=lambda: None, hook=hook)

    bound_handler = BoundHandler(hook, handler)
    assert bound_handler.hook is hook
    assert bound_handler._handler is handler

    bound_bound_handler = BoundHandler(hook, bound_handler)
    assert bound_bound_handler.hook is hook
    assert bound_bound_handler._handler is handler


def test_hook_kwarg_is_populated_with_bound_hook():
    the_hook = Hook()

    def handler(x, y, hook):
        assert x == 'x'
        assert y == 'y'
        assert hook is the_hook
        return x, y, hook

    the_hook(handler)
    assert the_hook.trigger(y='y', x='x') == [('x', 'y', the_hook)]


def test_calling_bound_handler_sets_triggering_context():
    the_hook = Hook()

    @the_hook
    def check_handler(hook):
        assert hook._is_triggering is True
        return 123

    assert the_hook.handlers[0]() == 123
