import collections
import functools
import inspect


class Registry:
    event_cls = None

    def __init__(self, event_cls=None, debug=False):
        self.event_cls = event_cls or self.event_cls
        self.events = collections.OrderedDict()
        self.event_log = []
        self.debug = debug

    def register_event(self, name, **kwargs):
        event_cls = kwargs.pop('event_cls', self.event_cls)
        event = event_cls(name, **kwargs)
        event.listener(functools.partial(self.log_event, event=event))
        self.events[event.name] = event
        return event

    def log_event(self, event):
        if self.debug:
            self.event_log.append(event.name)


class EventListener:
    def __init__(self, func=None, predicate=None):
        self.func = func
        self.predicate = predicate

        self._func_sig = None
        self._predicate_sig = None

    @property
    def func_sig(self) -> inspect.Signature:
        if self._func_sig is None and self.func is not None:
            self._func_sig = inspect.signature(self.func)
        return self._func_sig

    @property
    def predicate_sig(self) -> inspect.Signature:
        if self._predicate_sig is None and self.predicate is not None:
            self._predicate_sig = inspect.signature(self.predicate)
        return self._predicate_sig

    def __call__(self, func=None, **kwargs):
        if self.func is None:
            # Means, the listener is used as a decorator and is passed extra arguments
            assert callable(func)
            self.func = func
            assert not kwargs
            return self

        if self.predicate:
            predicate_kwargs = {k: v for k, v in kwargs.items() if k in self.predicate_sig.parameters}
            if not self.predicate(**predicate_kwargs):
                return

        func_kwargs = {k: v for k, v in kwargs.items() if k in self.func_sig.parameters}
        return self.func(**func_kwargs)

    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, self.func.__name__)


class Event:
    event_listener_cls = EventListener

    def __init__(self, name, **options):
        self.name = name
        self.event_listener_cls = options.pop('event_listener_cls', self.event_listener_cls)
        self.options = options
        self.listeners = []

    def __call__(self, *args, **kwargs):
        self.trigger(*args, **kwargs)

    def trigger(self, *args, **kwargs):
        for listener in self.listeners:
            listener(*args, **kwargs)

    def listener(self, func=None, predicate=None):
        event_listener = self.event_listener_cls(func=func, predicate=predicate)
        self.listeners.append(event_listener)
        return event_listener

    def __repr__(self):
        return '<{} {!r}>'.format(self.__class__.__name__, self.name)


Registry.event_cls = Event
