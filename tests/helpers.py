import dataclasses


@dataclasses.dataclass
class Call:
    name: str = None
    args: tuple = dataclasses.field(default_factory=tuple)
    kwargs: dict = dataclasses.field(default_factory=dict)

    def matches(self, name, *match_args, **match_kwargs):
        """
        Returns True if the name of the call matches, and args and kwargs of the call were
        the superset of the match_args and match_kwargs passed to this method.
        """
        if self.name != name:
            return False
        if match_args:
            len_args = len(match_args)
            if match_args != self.args[:len_args]:
                return False
        if match_kwargs:
            if not set(match_kwargs.items()).issubset(self.kwargs):
                return False
        return True


class Calls(list):
    def register(self, name, *args, **kwargs):
        self.append(Call(name, args, kwargs))
