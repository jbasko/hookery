# ------------------------------------------------------------------------
# ThingsService is the API you want your users to be able to hook into
# ------------------------------------------------------------------------

from hookery import HookRegistry


class ThingsService(object):
    def __init__(self):
        self._things = set()

        self._hooks = HookRegistry(self)
        self.thing_added = self._hooks.register_event('thing_added')
        self.thing_removed = self._hooks.register_event('thing_removed')

    def add(self, thing):
        self._things.add(thing)
        self.thing_added.trigger(things_service=self, thing=thing)

    def remove(self, thing):
        self._things.remove(thing)
        self.thing_removed.trigger(things_service=self, thing=thing)

# ------------------------------------------------------------------------
# This is how you hook into the API:
# ------------------------------------------------------------------------

service = ThingsService()


@service.thing_added
def added(thing):
    print('{} was added'.format(thing))


@service.thing_removed
def removed(thing, things_service):
    print('{} was removed, {} things remain'.format(thing, len(things_service._things)))


service.add(1)
service.add(2)
service.add(3)

service.remove(2)
