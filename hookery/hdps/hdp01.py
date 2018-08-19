class Hookable:
    pass


class Hook:
    # These are just placeholders to make IDE happy

    def __call__(self, *args, **kwargs):
        return args[0]

    def __get__(self, instance, owner):
        return self

    def handler(self, func):
        return func

    @property
    def handlers(self):
        return []


class Profile(Hookable):
    on_activated = Hook()

    @on_activated
    def log_activation(self):
        print(f"Activating {self}")

    @on_activated
    def validate_activation(self):
        print(f"Validating activation of {self}")

    def activate(self):
        self.on_activated()


class CustomProfile(Profile):
    on_customisation = Hook()

    @Profile.on_activated
    def log_activation(self):
        print(f"Activating CUSTOM {self}")

    @on_customisation
    def log_customisation(self):
        print(f"Customising {self}")


master = Profile()


@master.on_activated.handler
def on_master_profile_activated(profile):
    print(f"Activating master profile {profile}")


# List on_activated handlers associated with all Profile instances
print(Profile.on_activated.handlers)

# List on_activated handlers associated with all CustomProfile instances
print(CustomProfile.on_activated.handlers)

p = Profile()
# List on_activated handlers associated with p
print(p.on_activated.handlers)

c = CustomProfile()
# List on_activated handlers associated with c
print(c.on_activated.handlers)
