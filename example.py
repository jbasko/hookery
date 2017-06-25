from hookery import HookRegistry


class ThingsService(object):
    """
    ThingsService is the corner stone of your API and you want
    your users to be able to hook into it without extending the class.

    What you do is you create an internal hook registry and register two events
    that your API users can hook into:
    - thing_added
    - thing_removed

    """

    def __init__(self):
        self._things = set()
        self._hooks = HookRegistry(self)
        self.thing_added = self._hooks.register_event('thing_added')
        self.thing_removed = self._hooks.register_event('thing_removed')

    def add(self, thing):
        if thing not in self._things:
            self._things.add(thing)
            self.thing_added.trigger(thing=thing)

    def remove(self, thing):
        if thing in self._things:
            self._things.remove(thing)
            self.thing_removed.trigger(thing=thing)


things = ThingsService()


@things.thing_added
def added(thing):
    print('{} was just added'.format(thing))


@things.thing_removed
def removed(thing):
    print('{} was just removed'.format(thing))


if __name__ == '__main__':
    things.add(1)
    things.add(22)
    things.add(22)
    things.add(22)
    things.add(333)

    things.remove(4)
    things.remove(22)
