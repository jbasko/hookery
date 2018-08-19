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

---------------
Interface Style
---------------

There are two main ways to invoke the functionality we want:

* Instance attributes, instance methods

  .. code-block:: python

      from hookery import Hookable

      class Profile(Hookable):
          def activate(self):
              # many different ways ...

  To intercept any instance method calls we'd have to control the creation of the class and that means
  having a common base-class, or requiring the classes to be decorated with our decorator.

* Global functions which take any instances or classes as arguments and work out hooks and handlers
  at hook trigger time:

  .. code-block:: python

      from hookery import hooks

      class Profile:
          def activate(self):
              # or perhaps hooks.trigger(self.on_activated, *args, **kwargs) ?
              hooks.trigger('on_activated', self, *args, **kwargs)


The global functions approach is more flexible, seems simpler, and has so far been overlooked.

----------------------
Instance Hook Handlers
----------------------

Allow registration of a handler associated with a single instance of ``Profile``.

This would be the only way to register a handler when user is in no control of which class is used to build
their profile instances. If they cannot specify their ``CustomProfile`` class in which they would register
handlers then all they can do is register handlers for individual instances of ``Profile``.

.. code-block:: python

    # Yes, a "free-standing" function
    def log_activation(profile):
        print(f"Activating {profile}")

    # This syntax is just an example, it could be done differently!
    p1 = Profile()
    p1.on_activated.register_handler(log_activation)

    p2 = Profile()
    # p2 doesn't have log_activation registered as a handler

-----------------------
Hook Handler Inspection
-----------------------

User should be able to inspect all registered hook handlers for a class and for an instance.

--------------------
Required Limitations
--------------------

1. No Class-Associated Handler Registration Outside Class Body

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

1. There is no requirement to allow registering methods decorated with ``@classmethod`` or ``@staticmethod`` as handlers.

******************
Later Requirements
******************

1. Optional-argument-functions as hook handlers. Handler should be able to specify any arguments that it needs and
   not mention others.

2. Hooks of different types -- multi-value, no-return, middleware, mapping. There is probably no need for
   a first-value or a last-value hook:

   a. last-value hook, as we understand it, would only call and return the value returned by the last registered
      handler. This is the case with a normal instance method when user can choose to override a method and
      not call ``super()``, or even replace the method on the instance in question.

   b. first-value hook has no practical value -- it means do not override the method in question.
