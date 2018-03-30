import pytest

from hookery import ClassHook, hookable


def test_cannot_be_used_outside_class():
    before = ClassHook()

    with pytest.raises(TypeError):
        before.trigger()


def test_initialisation():
    @hookable
    class C:
        before = ClassHook()
        after = ClassHook()

    assert C.before.name == 'before'

    class D(C):
        pass

    assert D.before.name == 'before'

    assert C.before.subject is C
    assert D.before.subject is D

    C.before(lambda: 'C')
    D.before(lambda: 'D')

    with pytest.raises(TypeError):
        C().before(lambda: 'c')

    with pytest.raises(TypeError):
        D().before(lambda: 'd')

    assert D.before.trigger() == ['C', 'D']


def test_single_handler_hook():
    @hookable
    class C:
        before = ClassHook(single_handler=True)

    C.before(lambda: 1)
    assert C.before.trigger() == 1

    C.before(lambda: 2)
    assert C.before.trigger() == 2

    class D(C):
        pass

    D.before(lambda: 3)
    C.before(lambda: 4)

    # Last D's handler takes precedence over last C's handler
    assert D.before.trigger() == 3
