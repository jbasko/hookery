from hookery import Hook
from hookery.base import NoSubject, hookable


def test_initialisation():
    before = Hook()
    assert isinstance(before, Hook)
    assert before.name is None
    assert isinstance(before.subject, NoSubject)


def test_hookable_does_not_modify_standalone_hooks():
    @hookable
    class C:
        before = Hook()

    assert isinstance(C.before, Hook)
    assert C.before.subject is not C
    assert isinstance(C.before.subject, NoSubject)
    assert C.before.name is None

    assert C.before.trigger() == []

    C.before(lambda: 123)
    assert C.before.trigger() == [123]

    assert C().before is C.before


def test_standalone_hook_on_its_own():
    before = Hook()
    assert not before
    assert len(before.handlers) == 0
    assert before.trigger() == []

    before(lambda: 'handler1')
    before(lambda: 'handler2')

    assert before
    assert len(before.handlers) == 2
    assert before.trigger() == ['handler1', 'handler2']


def test_standalone_hook_on_an_instance_of_class():
    class C:
        def __init__(self):
            self.before = Hook()
            self.before(lambda: 'handler1')

    c = C()
    assert c.before
    assert c.before.trigger() == ['handler1']

    c.before(lambda: 'handler2')
    assert c.before.trigger() == ['handler1', 'handler2']


def test_unregister_handler():
    def handler1():
        return 'handler1'

    def handler2():
        return 'handler2'

    before = Hook()
    before(handler1)
    before(handler2)

    assert len(before.handlers) == 2
    assert before.trigger() == ['handler1', 'handler2']

    before.unregister_handler(handler1)
    assert len(before.handlers) == 1
    assert before.trigger() == ['handler2']

    before.unregister_handler(handler2)
    assert len(before.handlers) == 0
    assert before.trigger() == []
