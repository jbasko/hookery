import inspect

from hookery.base import Handler


def test_handler_from_func():
    def f(a, b):
        return a - b

    h = Handler(f, 'hook1')
    assert callable(h)
    assert h.__name__ == 'f'
    assert h.name == 'f'
    assert h.hook_name == 'hook1'
    assert not h.is_generator
    assert h(c=8, b=10, a=25) == 15
    assert h.get_result(b=5, a=10) == 5
    assert h.get_result(10, 5) == 5


def test_handler_from_generator():
    def g(a, b):
        yield 2 * a
        yield 3 * b

    h = Handler(g, 'hook2')
    assert h.hook_name == 'hook2'
    assert h.is_generator
    assert inspect.isgenerator(h())
    assert list(h(5, 6)) == [10, 18]
    assert h.get_result(5, 6) == [10, 18]
