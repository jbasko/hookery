from hookery import Handler, Hook


def test_handler_from_func():
    def f(a, b):
        return a - b

    h = Handler(f, Hook('hook1'))
    assert callable(h)
    assert h.__name__ == 'f'
    assert h.name == 'f'
    assert h.hook_name == 'hook1'
    assert not h.is_generator
    assert h(c=8, b=10, a=25) == 15
    assert h(b=5, a=10) == 5


def test_handler_of_handler_uses_original_func_as_original_func():
    def f(a, b):
        return a + b

    handler1 = Handler(f, Hook('hook'))

    assert handler1._original_func is f

    handler2 = Handler(handler1, Hook('hook'))

    assert handler2._original_func is f
    assert handler1._original_func is f
