from hookery.v1 import Event, HookRegistry


def test_registry_wide_event_cls():
    calls = []

    class CustomEvent(Event):
        pass

    hooks = HookRegistry(event_cls=CustomEvent)
    e1 = hooks.register_event('e1')
    assert isinstance(e1, CustomEvent)

    @e1
    def listener(*args, **kwargs):
        calls.append((args, kwargs))

    e1.trigger()
    assert len(calls) == 1


def test_event_specific_event_cls():
    class CustomEvent(Event):
        pass

    hooks = HookRegistry()
    e1 = hooks.register_event('e1', event_cls=CustomEvent)
    assert isinstance(e1, CustomEvent)


def test_custom_event_that_gets_triggered_only_with_certain_kwargs():
    class ValueChangedEvent(Event):

        def __call__(self, name):
            assert isinstance(name, str)
            the_name = name

            def decorator(f):
                # Do not use functools.wraps here because you actually want the registered function
                # to have a different signature from the callback's signature -- we need "name"
                # to be injected.
                def hook_func(name):
                    if name == the_name:
                        return f()
                hook_func.__name__ = f.__name__
                return self.register_hook(hook_func)

            return decorator

    hooks = HookRegistry()
    value_changed = hooks.register_event('value_changed', event_cls=ValueChangedEvent)

    changes = []

    @value_changed(name='x')
    def x_changed():
        changes.append('x')

    @value_changed(name='y')
    def y_changed():
        changes.append('y')

    value_changed.trigger(name='x')
    assert changes == ['x']

    value_changed.trigger(name='x')
    assert changes == ['x', 'x']

    value_changed.trigger(name='y')
    assert changes == ['x', 'x', 'y']
