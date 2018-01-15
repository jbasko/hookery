import pytest

from hookery import Event, Registry


@pytest.fixture
def registry():
    return Registry(event_cls=Event, debug=True)


@pytest.fixture
def dummy_event_one(registry):
    return registry.register_event('dummy_event_one')


def test_event_repr(dummy_event_one):
    assert repr(dummy_event_one) == "<Event 'dummy_event_one'>"


def test_event_listener_repr(dummy_event_one):
    @dummy_event_one.listener
    def listener():
        pass

    assert repr(listener) == "<EventListener 'listener'>"


def test_default_event_cls_is_event():
    assert Registry.event_cls is Event


def test_registry_has_event_cls_set(registry: Registry):
    assert registry.event_cls is Event


def test_register_event_returns_instance_of_event_cls(registry: Registry):
    event = registry.register_event('value_changed')
    assert isinstance(event, Event)


def test_event_listener_is_a_decorator_to_register_listener(dummy_event_one: Event):
    def cb(*args, **kwargs):
        pass

    listener1 = dummy_event_one.listener(cb)
    listener2 = dummy_event_one.listener(cb)

    assert [listener1, listener2] == dummy_event_one.listeners[-2:]
    assert listener1.func is cb
    assert listener2.func is cb


def test_calling_event_and_calling_trigger_triggers_the_event(registry: Registry, dummy_event_one: Event):
    dummy_event_one()
    assert registry.event_log == ['dummy_event_one']

    dummy_event_one.trigger()
    assert registry.event_log == ['dummy_event_one', 'dummy_event_one']


def test_each_listener_gets_what_kwargs_it_wants(dummy_event_one: Event):
    log = []

    @dummy_event_one.listener
    def needs_x(x):
        log.append(('x', x))

    @dummy_event_one.listener
    def needs_y(y):
        log.append(('y', y))

    @dummy_event_one.listener
    def needs_both(x, y):
        log.append(('xy', (x, y)))

    dummy_event_one(x=1, y=2, z=3)

    assert log == [('x', 1), ('y', 2), ('xy', (1, 2))]


def test_listener_with_conditions(dummy_event_one: Event):
    calls = []

    @dummy_event_one.listener(predicate=lambda name: name.startswith('interesting_'))
    def listener(name):
        calls.append(name)

    dummy_event_one.trigger(name='interesting_one')
    dummy_event_one.trigger(name='boring_one')
    dummy_event_one.trigger(name='boring_two')
    dummy_event_one.trigger(name='interesting_two')

    assert calls == ['interesting_one', 'interesting_two']
