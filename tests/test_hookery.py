import time

from hookery import HookRegistry


def test_e2e():

    class Collection(object):
        def __init__(self):
            self._hooks = HookRegistry(self)
            self._data = set()
            self.item_added = self._hooks.register_event('item_added')
            self.item_removed = self._hooks.register_event('item_removed')

        def add(self, item):
            self._data.add(item)
            self._hooks.handle(self.item_added, item=item, timestamp=time.time())

        def remove(self, item):
            self._data.remove(item)
            self._hooks.handle(self.item_removed, item=item, timestamp=time.time())

    bag = Collection()

    calls = []

    @bag.item_added
    def item_added(item, timestamp):
        assert isinstance(timestamp, float)
        assert item == 'hello'
        calls.append('first')

    @bag.item_added
    def item_added(timestamp, item):
        assert isinstance(timestamp, float)
        assert item == 'hello'
        calls.append('second')
        return True

    @bag.item_added
    def item_added(timestamp, item):
        assert isinstance(timestamp, float)
        assert item == 'hello'
        calls.append('third')

    @bag.item_removed
    def item_removed(item):
        assert item == 'hello'
        calls.append('removed')

    assert len(calls) == 0

    bag.add('hello')
    assert len(calls) == 2
    assert calls == ['first', 'second']

    bag.add('hello')
    assert len(calls) == 4
    assert calls[-2:] == ['first', 'second']

    bag.remove('hello')
    assert len(calls) == 5
    assert calls[-1] == 'removed'

    # Change the stop condition, just for the purposes of testing
    bag.item_added.stop_condition = lambda result: False

    bag.add('hello')
    assert len(calls) == 8
    assert calls[-3:] == ['first', 'second', 'third']


def test_hook_registered_hook():
    hooks = HookRegistry()

    hooks_registered = []

    @hooks.hook_registered
    def hook_registered(event, hook):
        hooks_registered.append(('hook_registered', event, hook.__name__))

    assert len(hooks_registered) == 0

    something_happened = hooks.register_event('something_happened')

    assert len(hooks_registered) == 0

    @something_happened
    def first_hook():
        pass

    assert len(hooks_registered) == 1

    @something_happened
    def second_hook():
        pass

    assert len(hooks_registered) == 2

    assert hooks_registered == [
        ('hook_registered', 'something_happened', 'first_hook'),
        ('hook_registered', 'something_happened', 'second_hook'),
    ]
