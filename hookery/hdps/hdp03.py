class hooks:  # Just to simulate a module called "hooks"
    @staticmethod
    def trigger(bound_hook, *args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def get_handlers(hook):
        raise NotImplementedError()


class HookBase:
    pass


class BoundHook(HookBase):
    def __init__(self, hook, owner):
        self._hook = hook
        self._owner = owner

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()


class ClassHook(BoundHook):
    def __init__(self, hook, owner):
        super().__init__(hook, owner)
        self._class_handlers = []

    def __call__(self, func):
        self._class_handlers.append(func)


class InstanceHook(BoundHook):
    def __init__(self, hook, owner):
        super().__init__(hook, owner)
        self._instance_handlers = []

    def __call__(self, func):
        self._instance_handlers.append(func)


class Hook(HookBase):
    def __init__(self):
        self.name = None
        self._owner_handlers = []

    def __set_name__(self, owner, name):
        self.name = name

    def __call__(self, func):
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
    def log_activation(self):
        print(f"Activating CUSTOM {self}")

    @on_customisation
    def log_customisation(self):
        print(f"Customising {self}")


master = Profile()


@master.on_activated
def on_master_profile_activated(profile):
    print(f"Activating master profile {profile}")


master.activate()


# List on_activated handlers associated with all Profile instances
print(hooks.get_handlers(Profile.on_activated))

# List on_activated handlers associated with all CustomProfile instances
print(hooks.get_handlers(CustomProfile.on_activated))

p = Profile()
# List on_activated handlers associated with p
print(hooks.get_handlers(p.on_activated))

c = CustomProfile()
# List on_activated handlers associated with c
print(hooks.get_handlers(c.on_activated))
