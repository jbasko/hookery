import functools
import inspect
from typing import Any, List


class hooks:
    """
    Just a namespace to keep all helpers under one roof.
    """

    @staticmethod
    def get_handlers(hook: "BoundHook"):
        return hook.get_handlers()

    @staticmethod
    def trigger(hook: "BoundHook", *args, **kwargs):
        assert isinstance(hook, InstanceHook)
        for handler in hooks.get_handlers(hook):
            handler(*args, **kwargs)

    @staticmethod
    def get_hooks(hookable: Any) -> List["BoundHook"]:
        # TODO Should probably maintain order!
        return list({h for _, h in inspect.getmembers(hookable, predicate=lambda m: isinstance(m, BoundHook))})

    @staticmethod
    def exists_hook(cls, hook_name):
        return isinstance(getattr(cls, hook_name, None), BoundHook)


class HookBase:
    pass


class BoundHook(HookBase):
    def __init__(self, hook: "Hook", owner):
        self._base_hook = hook  # type: Hook
        self._owner = owner

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def base_hook(self) -> "Hook":
        return self._base_hook

    @property
    def name(self):
        return self.base_hook.name

    def get_handlers(self):
        """
        Handlers can come from:
        1) the class in which the hook is declared
        2) subclass_handlers
        3) instance_handlers if hook is an InstanceHook
        """
        raise NotImplementedError()


class ClassHook(BoundHook):
    def __init__(self, hook, owner):
        super().__init__(hook, owner)

        # Subclass handlers do not apply to the instances of this class but only
        # to the instances of its subclasses.
        self._subclass_handlers = []

    def __call__(self, func):
        """
        You cannot register handlers on a class that has already been created.
        Handlers registered in this way will only apply to sub-classes of this class.
        """
        self._subclass_handlers.append(func)
        return func

    @property
    def is_inherited(self):
        return self.base_hook._owner is not self._owner

    def _get_handlers(self):
        # Yield handlers which are registered in the class which declares the hook.
        for handler in self.base_hook._unbound_handlers:
            yield handler

        # For inherited hooks go through all classes in the mro between the class that
        # declares this hook and this class and yield all subclass handlers.
        if self.is_inherited:
            mro = inspect.getmro(self._owner)

            # Consider class hierarchy: C < D < E; C < F.
            # D, E and F can all be registering handlers against C.hook_x
            # which means that C.hook_x._subclass_handlers contains a union of handlers for D, E, F.
            # Some handlers in this list are not for D, some are not for E, some are not for F.
            # How we check which ones are is by looking into all classes in class's mro
            # and comparing the class's handler-named attribute with the handler.
            # If it's an exact match, we know the handler comes from that class, so we are good to yield it.
            # + TODO We don't have a test for this...
            # + We do cls.__dict__.get(...) because getattr(cls, ...) might return handler from parent class
            # + and then we'd have duplicates.
            is_in_mro = lambda func: any(cls.__dict__.get(func.__name__, None) is func for cls in mro)  # noqa

            for cls in reversed(mro[1:-1]):  # exclude owner class and object
                if hooks.exists_hook(cls, self.name):
                    for subclass_handler in getattr(cls, self.name)._subclass_handlers:
                        # if subclass_handler is getattr(self._owner, subclass_handler.__name__, None):
                        if is_in_mro(subclass_handler):
                            yield subclass_handler

    def get_handlers(self):

        # Remove duplicates and convert to a list.
        # TODO Not sure there can be duplicates now. Need a test or remove this code.
        seen = set()
        handlers = []
        for handler in self._get_handlers():
            if handler not in seen:
                seen.add(handler)
                handlers.append(handler)
        return handlers


class InstanceHook(BoundHook):
    def __init__(self, hook, owner):
        super().__init__(hook, owner)
        self._instance_handlers = []

    def __call__(self, func):
        self._instance_handlers.append(func)

    @property
    def class_hook(self) -> ClassHook:
        return getattr(self._owner.__class__, self.name)

    def _get_handlers(self):
        for handler in self.class_hook.get_handlers():
            yield functools.partial(handler, self._owner)
        for handler in self._instance_handlers:
            yield functools.partial(handler, self._owner)

    def get_handlers(self):
        return list(self._get_handlers())


class Hook(HookBase):
    """
    Unbound hook.

    These objects are mutable only for the duration of class body parsing in which they are declared.
    Once class is ready (the owner for this object is set via ``__set_name__`` hook),
    no more handlers can be registered.
    """

    def __init__(self):
        self.name = None
        self._owner = None
        self._unbound_handlers = []

    def __set_name__(self, owner, name):
        self.name = name

        # Setting of the owner marks the end of mutability for this object.
        self._owner = owner

    def __call__(self, func):
        """
        Register handler
        """
        if self._owner is not None:
            raise RuntimeError(f"Cannot register handlers on a finalised {self}")
        self._unbound_handlers.append(func)
        return func

    @property
    def _name_in_dict(self):
        assert self.name
        return f"hook#{self.name}"

    def __get__(self, instance, owner) -> BoundHook:
        if instance is None:
            if self._name_in_dict not in owner.__dict__:
                setattr(owner, self._name_in_dict, ClassHook(hook=self, owner=owner))
            return getattr(owner, self._name_in_dict)
        else:
            if self._name_in_dict not in instance.__dict__:
                setattr(instance, self._name_in_dict, InstanceHook(hook=self, owner=instance))
            return getattr(instance, self._name_in_dict)
