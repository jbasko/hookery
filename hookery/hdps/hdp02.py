class Hookable:
    pass


class HookSpec:
    pass


class Profile(Hookable):
    class Hooks(HookSpec):
        def on_activated(self):
            pass

    @Hooks.on_activated
    def log_activation(self):
        print(f"Activating {self}")

    @Hooks.on_activated
    def validate_activation(self):
        print(f"Validating activation of {self}")

    def activate(self):
        self.Hooks.on_activated.trigger()


class CustomProfile(Profile):

    class Hooks(Profile.Hooks):
        def on_customisation(self):
            pass

    @Profile.Hooks.on_activated  # Or @Hooks.on_activation
    def log_activation(self):
        print(f"Activating CUSTOM {self}")

    @Hooks.on_customisation
    def log_customisation(self):
        print(f"Customising {self}")


master = Profile()


@master.Hooks.on_activated
def on_master_profile_activated(profile):
    print(f"Activating master profile {profile}")


# List on_activated handlers associated with all Profile instances
print(Profile.Hooks.on_activated.handlers)

# List on_activated handlers associated with all CustomProfile instances
print(CustomProfile.Hooks.on_activated.handlers)

p = Profile()
# List on_activated handlers associated with p
print(p.Hooks.on_activated.handlers)

c = CustomProfile()
# List on_activated handlers associated with c
print(c.Hooks.on_activated.handlers)
