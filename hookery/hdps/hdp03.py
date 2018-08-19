class hooks:  # Just to simulate a module called "hooks"

    @staticmethod
    def get_handlers(hook: "BoundHook"):
        return hook.get_handlers()

    @staticmethod
    def trigger(hook: "BoundHook", *args, **kwargs):
        assert isinstance(hook, InstanceHook)
        print(f"Triggering {hook}")
        print(hooks.get_handlers(hook))
        raise NotImplementedError()


class HookBase:
    pass


class BoundHook(HookBase):
    def __init__(self, hook: "Hook", owner):
        self._hook = hook  # type: Hook
        self._owner = owner

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    @property
    def name(self):
        return self._hook.name

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
        setattr(func, '_is_subclass_handler', True)
        return func


class InstanceHook(BoundHook):
    def __init__(self, hook, owner):
        super().__init__(hook, owner)
        self._instance_handlers = []

    def __call__(self, func):
        self._instance_handlers.append(func)

    @property
    def class_hook(self) -> ClassHook:
        return getattr(self._owner.__class__, self.name)

    def get_handlers(self):
        print(self._hook._owner_handlers)
        print(self.class_hook._subclass_handlers)
        print(self._instance_handlers)
        raise NotImplementedError()


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
        self._owner_handlers = []

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
        self._owner_handlers.append(func)

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


class Profile:
    on_activated = Hook()

    @on_activated
    def log_activation(self):
        print(f"Activating {self}")

    @on_activated
    def validate_activation(self):
        print(f"Validating activation of {self}")

    def activate(self, *args, **kwargs):
        hooks.trigger(self.on_activated, *args, **kwargs)


class CustomProfile(Profile):
    on_customisation = Hook()

    @Profile.on_activated
    def log_activation_by_custom_profile(self):
        print(f"Activating CUSTOM {self}")

    @on_customisation
    def log_customisation(self):
        print(f"Customising {self}")


# print('Profile')
# print(Profile.on_activated.__dict__)
# print(Profile.on_activated._hook.__dict__)
#
# print('CustomProfile')
# print(CustomProfile.on_activated.__dict__)
# print(CustomProfile.on_activated._hook.__dict__)

master = CustomProfile()


# @master.on_activated
# def on_master_profile_activated(profile):
#     print(f"Activating master profile {profile}")


master.activate()


# # List on_activated handlers associated with all Profile instances
# print(hooks.get_handlers(Profile.on_activated))
#
# # List on_activated handlers associated with all CustomProfile instances
# print(hooks.get_handlers(CustomProfile.on_activated))
#
# p = Profile()
# # List on_activated handlers associated with p
# print(hooks.get_handlers(p.on_activated))
#
# c = CustomProfile()
# # List on_activated handlers associated with c
# print(hooks.get_handlers(c.on_activated))
