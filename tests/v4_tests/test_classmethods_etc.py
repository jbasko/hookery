from hookery.v4 import HookSpec, Hook


class MyHooks(HookSpec):
    before = Hook()


def test_classmethod_as_hook():
    my_hooks = MyHooks()

    class Base:
        @classmethod
        @my_hooks.before
        def before(cls):
            return 'classmethod.before'

    # print(my_hooks.before.get_handlers())
    print(my_hooks.__dict__)
    assert my_hooks.before.trigger() == ['classmethod.before']

    # raise NotImplementedError()


def test_staticmethod_as_hook():
    my_hooks = MyHooks()

    class Base:
        @my_hooks.before
        @staticmethod
        def before():
            return 'staticmethod.before'

    raise NotImplementedError()

