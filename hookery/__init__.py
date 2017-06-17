import collections

try:
    from inspect import signature
except ImportError:
    from funcsigs import signature


class Event(object):
    def __init__(self, name, register_func=None, trigger_func=None, unregister_func=None, stop_condition=None):
        self.name = name
        self._register_func = register_func
        self._unregister_func = unregister_func
        self._trigger_func = trigger_func

        if stop_condition is None:
            self.stop_condition = lambda result: result is not None
        elif callable(stop_condition):
            self.stop_condition = stop_condition
        else:
            self.stop_condition = lambda result, sc=stop_condition: result == sc

    def __call__(self, hook_func):
        return self.register_hook(hook_func)

    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, self.name)

    def register_hook(self, hook_func):
        if not callable(self._register_func):
            raise RuntimeError('Event {!r} does not support hook registration'.format(self.name))

        registered_hook_func = self._register_func(self.name, hook_func)
        if not callable(registered_hook_func):
            raise RuntimeError(
                'Invalid hook registration function {} - it did not return the hook'.format(self._register_func)
            )

        return registered_hook_func

    def unregister_hook(self, hook_func):
        if not callable(self._unregister_func):
            raise RuntimeError('Event {!r} does not support hook unregistration'.format(self.name))
        return self._unregister_func(self.name, hook_func)

    def trigger(self, **kwargs):
        if self._trigger_func is None:
            raise RuntimeError('Event {!r} cannot be triggered'.format(self.name))
        self._trigger_func(self, **kwargs)


class HookRegistry(object):
    def __init__(self, owner=None):
        self._owner = owner

        self._events = {}
        self._hooks = collections.defaultdict(list)

        # Internal event names start with double underscore
        self.hook_registered = self.register_event('__hook_registered')

    def register_event(self, name, **kwargs):
        if name in self._events:
            raise ValueError('Event {!r} already registered'.format(name))

        kwargs.setdefault('register_func', self.register_hook)
        kwargs.setdefault('trigger_func', self.dispatch_event)
        kwargs.setdefault('unregister_func', self.unregister_hook)

        event = Event(name=name, **kwargs)
        self._events[name] = event

        return event

    def register_hook(self, event_name, hook):
        assert callable(hook)
        if isinstance(event_name, Event):
            event_name = event_name.name
        assert event_name in self._events
        self._hooks[event_name].append((signature(hook), hook))
        if not event_name.startswith('__'):
            self.hook_registered.trigger(event=self._events[event_name], hook=hook)
        return hook

    def unregister_hook(self, event_name, hook):
        if isinstance(event_name, Event):
            event_name = event_name.name

        remaining_hooks = []
        for h_sig, h_func in self._hooks[event_name]:
            if hook != h_func:
                remaining_hooks.append((h_sig, h_func))

        if len(remaining_hooks) == len(self._hooks[event_name]):
            raise ValueError('Cannot unregister unknown hook {}'.format(hook))

        self._hooks[event_name] = remaining_hooks

    def dispatch_event(self, event_, **kwargs):
        if isinstance(event_, Event):
            event_name = event_.name
        else:
            event_name = event_

        event_ = self._events[event_name]

        result = None

        for hook_signature, hook in self._hooks[event_.name]:

            # Collect kwargs which the hook is interested in.
            # If hook wants **kwargs, that means it is interested in all,
            # otherwise pass only the mentioned ones.

            hook_kwargs = None
            for _, param in hook_signature.parameters.items():
                if param.kind == param.VAR_KEYWORD:
                    hook_kwargs = kwargs

            if hook_kwargs is None:
                hook_kwargs = {}
                for param in kwargs:
                    if param in hook_signature.parameters:
                        hook_kwargs[param] = kwargs[param]

            # Prepare args and kwargs for the hook
            bound_args = hook_signature.bind_partial(**hook_kwargs)

            # Call the hook
            result = hook(*bound_args.args, **bound_args.kwargs)

            # Decide whether we should continue
            if event_.stop_condition(result):
                return result

        return result

    def __getitem__(self, event):
        """
        Returns list of hooks registered for the specified event
        """
        if isinstance(event, Event):
            event = event.name
        return self._hooks[event]
