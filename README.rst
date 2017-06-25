*******
hookery
*******

.. code-block:: shell

    pip install hookery


It's really simple. There are some events in the lifetime of your simple Python application that you want to hook into,
and you don't want to be overriding methods or writing conditional code to do that. What you do is you
introduce events and register hooks.

Quick Start
===========

Let's assume that ``ThingsService`` class is the corner stone of your API.
This service allows adding things and removing them:

.. code-block:: python

    class ThingsService(object):
        def __init__(self):
            self._things = set()

        def add(thing):
            self._things.add(thing)

        def remove(thing)
            self._things.remove(thing)

You wish users of your API to be able to execute their code when a thing is added or removed, but you don't
want them to be extending your service class to do that.

What you do is you create an internal hook registry inside ``ThingsService`` and register two events that you wish
your users to hook into, and expose them on your service class so that users can use them as decorators to register
their hooks:

.. code-block:: python
    :emphasize-lines: 2, 8-10, 14, 18

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


Your API users can now register their hooks and be notified of all the latest updates from the things service:

.. code-block:: python

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
