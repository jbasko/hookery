************
Requirements
************

Given a class ``Profile`` which has instance method ``activate()``, we would like to allow a user of this class
to extend it and enrich its functionality by use of a hook: ``on_activated``.

The user should be able to register handlers associated with this hook. Handlers should be instance methods
of the ``Profile`` class or any class that extends it.

Ideally, it should be clear to any reader of the extended class's code that the methods registered as handlers
are special and are not to be called directly.

Handlers associated with ``on_activated`` hook are called from ``Profile.activate()`` (which users aren't meant
to override).

Developers of the ``Profile`` class should be able to trigger the handlers of ``on_activated`` hook
in a readable fashion.

A user extending the ``Profile`` class or using instances of it should have the name of the available hook
(``on_activated``) suggested by their IDE (PyCharm).


.. code-block:: python

    class Profile:
        # Specify that there is a hook called "on_activated"
        # ...

        # Register zero or more handlers associated with the "on_activated" hook
        # ...

        def activate():
            # Trigger handlers of the on_activated hook.
            pass


    class CustomProfile(Profile):
        # Register zero or more handlers associated with the "on_activated" hook

        # Specify additional hooks that this custom profile exposes.


--------------------
Required Limitations
--------------------

1. No Handler Registration Outside Class Body

   It should not be allowed to register functions that are not instance methods as hook handlers because it complicates
   thinking about the class functionality. The class's behaviour then depends on what handlers have been loaded.

   ``@Profile.on_activated`` decorator syntax is just one of many ways of how the registration could be done.
   It is not a requirement itself.

   .. code-block:: python

       # THIS IS BAD!

       @Profile.on_activated
       def log_activation(profile):
           print(f"Activating {profile}")


   If the user has to modify ``Profile`` behaviour, they should extend the class and register handlers on the new class.

   Again, ``@Profile.on_activated`` decorator syntax is just one of many ways this could be done.
   The key is that ``log_activation`` must be declared inside class body.

   .. code-block:: python

       # This is better.

       class AppProfile(Profile):

           @Profile.on_activated
           def log_activation(self):
               print(f"Activating {self}")


****************
Not Requirements
****************

1. There is no requirement to allow registering a handler associated with a single instance of ``Profile``
   class, but if it can be done, why not!

.. code-block:: python

    # Yes, a "free-standing" function
    def log_activation(profile):
        print(f"Activating {profile}")

    # This syntax is just an example, it could be done differently!
    p1 = Profile()
    p1.on_activated.register_handler(log_activation)

    p2 = Profile()
    # p2 doesn't have log_activation registered as a handler


2. There is no requirement to allow registering methods decorated with ``@classmethod`` or ``@staticmethod`` as handlers.
