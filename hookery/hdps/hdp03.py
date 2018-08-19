class hooks:  # Just to simulate a module called "hooks"
    @staticmethod
    def trigger(bound_hook, *args, **kwargs):
        pass

    @staticmethod
    def get_handlers(hook):
        return []


class Hook:
    def __call__(self, *args, **kwargs):
        return args[0]


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
