import collections

try:
    from inspect import signature
except ImportError:
    from funcsigs import signature


class Hook(object):
    def __init__(self, name, registry, stop_condition=None):
        self.name = name
        self.registry = registry

        if stop_condition is None:
            self.stop_condition = lambda result: result is not None
        elif callable(stop_condition):
            self.stop_condition = stop_condition
        else:
            self.stop_condition = lambda result, sc=stop_condition: result == sc

    def __call__(self, f):
        self.registry.register_callback(self.name, f)


class HookRegistry(object):
    def __init__(self, owner=None):
        self._owner = owner
        self._callbacks = collections.defaultdict(list)
        self._hooks = {}

    def create_hook(self, name):
        assert name not in self._hooks
        hook = Hook(name, self)
        self._hooks[name] = hook
        return hook

    def register_callback(self, name, callback):
        assert name in self._hooks
        assert callable(callback)
        self._callbacks[name].append((signature(callback), callback))

    def handle(self, hook, **kwargs):
        if isinstance(hook, Hook):
            assert self._hooks[hook.name] is hook
        else:
            hook = self._hooks[hook]

        result = None

        for cb_signature, cb in self._callbacks[hook.name]:

            # Collect kwargs which the callback is interested in
            cb_kwargs = {}
            for param in kwargs:
                if param in cb_signature.parameters:
                    cb_kwargs[param] = kwargs[param]

            # Prepare args and kwargs for the callback
            bound_args = cb_signature.bind_partial(**cb_kwargs)

            # Call the callback
            result = cb(*bound_args.args, **bound_args.kwargs)

            # Decide whether we should continue
            if hook.stop_condition(result):
                return result

        return result
