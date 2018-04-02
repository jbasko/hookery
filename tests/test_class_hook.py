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

    assert C.before.subject is C
    assert C.before.name == 'before'

    assert C.after.subject is C
    assert C.after.name == 'after'

    class D(C):
        pass

    assert D.before.subject is D
    assert D.before.name == 'before'

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


def test_defining_class():
    @hookable
    class C:
        before = ClassHook()

    class D(C):
        pass

    class E(D):
        pass

    assert C.before.defining_class is C
    assert C().before.defining_class is C
    assert D.before.defining_class is C
    assert D().before.defining_class is C
    assert E.before.defining_class is C
    assert E().before.defining_class is C


def test_hook_is_protected_from_accidental_overwrite_by_same_name_handler():
    @hookable
    class B:
        before = ClassHook()

    with pytest.raises(RuntimeError):
        class C(B):
            @B.before
            def before(self):
                pass
