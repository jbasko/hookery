import time

import pytest

from hookery import HookRegistry, Event


def test_event_is_a_decorator():
    a_event = Event('a_event', register_func=lambda event, hook: hook)

    assert a_event.name == 'a_event'
    assert callable(a_event)

    def f1():
        pass

    f2 = lambda x: x

    assert a_event(f1) is f1
    assert a_event(f2) is f2


def test_register_event_returns_event():
    event = HookRegistry().register_event('a_event')
    assert isinstance(event, Event)


def test_register_hook_returns_what_equals_hook_function_itself():
    registry = HookRegistry()
    registry.register_event('a_event')

    def hook_func(x):
        return x

    assert registry.register_hook('a_event', hook_func) == hook_func


def test_e2e():

    class Collection(object):
        def __init__(self):
            self._hooks = HookRegistry(self)
            self._data = set()
            self.item_added = self._hooks.register_event('item_added')
            self.item_removed = self._hooks.register_event('item_removed')

        def add(self, item):
            self._data.add(item)
            self._hooks.dispatch_event(self.item_added, item=item, timestamp=time.time())

        def remove(self, item):
            self._data.remove(item)
            self._hooks.dispatch_event(self.item_removed, item=item, timestamp=time.time())

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
        hooks_registered.append(('hook_registered', event.name, hook.__name__))

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


def test_hook_with_kwargs_gets_all_event_kwargs():
    hooks = HookRegistry()
    hooks.event1 = hooks.register_event('event1')

    calls = []

    @hooks.event1
    def event1_handler1(**kwargs):
        assert kwargs == {'a': 1,  'b': 2, 'c': 3, 'd': 4}
        calls.append('handler1')

    @hooks.event1
    def event1_handler2(c, d):
        assert c == 3
        assert d == 4
        calls.append('handler2')

    assert len(calls) == 0

    hooks.dispatch_event('event1', a=1, b=2, c=3, d=4)

    assert len(calls) == 2


def test_event_register_hook_and_trigger_methods():
    hooks = HookRegistry()

    calls = []

    event1 = hooks.register_event('event1')

    @event1
    def handle_event(id):
        calls.append(id)
        return 'result{}'.format(id)

    result = event1.trigger(id=1)
    assert calls == [1]
    assert result == 'result1'

    result = event1.trigger(id=2)
    assert calls == [1, 2]
    assert result == 'result2'


def test_unregister_hook():
    hooks = HookRegistry()

    calls = []

    a_event = hooks.register_event('a_event')

    @a_event
    def x_hook(id):
        calls.append('x{}'.format(id))

    @a_event
    def y_hook(id):
        calls.append('y{}'.format(id))

    a_event.trigger(id=1)
    a_event.trigger(id=2)

    assert calls == ['x1', 'y1', 'x2', 'y2']

    hooks.unregister_hook(a_event, x_hook)

    a_event.trigger(id=3)
    a_event.trigger(id=4)

    assert calls == ['x1', 'y1', 'x2', 'y2', 'y3', 'y4']


def test_registers_and_unregisters_hook_which_is_an_instance_method():
    registry = HookRegistry()
    registry.register_event('a_event')

    class MyClass(object):
        def hook_method(self):
            pass

    my_instance = MyClass()
    registered_hook = registry.register_hook('a_event', my_instance.hook_method)
    assert registered_hook == my_instance.hook_method

    # But:
    assert registered_hook is not my_instance.hook_method

    assert len(registry['a_event']) == 1

    # Try unregistered with what was returned by register_hook
    registry.unregister_hook('a_event', registered_hook)
    assert len(registry['a_event']) == 0

    # Register again and unregister with the original method reference
    registry.register_hook('a_event', my_instance.hook_method)
    assert len(registry['a_event']) == 1
    registry.unregister_hook('a_event', my_instance.hook_method)
    assert len(registry['a_event']) == 0


def test_unregister_hook_raises_exception_for_unknown_hooks():
    registry = HookRegistry()
    a_event = registry.register_event('a_event')

    def hook():
        pass

    # Through registry

    assert len(registry[a_event]) == 0

    with pytest.raises(ValueError):
        registry.unregister_hook(a_event, hook)

    registry.register_hook(a_event, hook)
    assert len(registry[a_event]) == 1

    registry.unregister_hook(a_event, hook)
    assert len(registry[a_event]) == 0

    with pytest.raises(ValueError):
        registry.unregister_hook(a_event, hook)

    # Directly on event instance

    with pytest.raises(ValueError):
        a_event.unregister_hook(hook)

    a_event.register_hook(hook)
    assert len(registry[a_event]) == 1

    a_event.unregister_hook(hook)
    assert len(registry[a_event]) == 0

    with pytest.raises(ValueError):
        a_event.unregister_hook(hook)
