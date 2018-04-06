import inspect

from hookery.base import GlobalHook, Handler, InstanceHook


def test_handler_from_func():
    def f(a, b):
        return a - b

    h = Handler(f, GlobalHook('hook1'))
    assert callable(h)
    assert h.__name__ == 'f'
    assert h.name == 'f'
    assert h.hook_name == 'hook1'
    assert not h.is_generator
    assert h(c=8, b=10, a=25) == 15
    assert h(b=5, a=10) == 5


def test_handler_from_generator():
    def g(a, b):
        yield 2 * a
        yield 3 * b

    hook2 = GlobalHook('hook2')
    handler = Handler(g, hook2)
    assert handler.hook_name == 'hook2'
    assert handler.is_generator
    assert inspect.isgenerator(handler())
    assert list(handler(a=5, b=6)) == [10, 18]
    assert hook2.get_result_from_handler(handler, a=5, b=6) == [10, 18]


def test_instance_hook_handler_from_bound_method():
    class C:
        def parse(self, value):
            assert isinstance(self, C)
            return value * 5

    hook = InstanceHook('before')
    handler = Handler(C().parse, hook=hook)
    assert handler(value=6) == 30
    assert hook.get_result_from_handler(handler, value=6) == 30


def test_handler_of_handler_uses_original_func_as_original_func():
    def f(a, b):
        return a + b

    handler1 = Handler(f, GlobalHook('hook'))

    assert handler1._original_func is f

    handler2 = Handler(handler1, GlobalHook('hook'))

    assert handler2._original_func is f
    assert handler1._original_func is f
