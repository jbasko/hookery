import functools
import inspect
from typing import Any, List


class hooks:  # Just to simulate a module called "hooks"

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
        # TODO See docs/hpds/03.rst !!!
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
            for cls in reversed(inspect.getmro(self._owner)[1:-1]):  # exclude owner class and object
                if hooks.exists_hook(cls, self.name):
                    yield from getattr(cls, self.name)._subclass_handlers

    def get_handlers(self):
        return list(self._get_handlers())


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
