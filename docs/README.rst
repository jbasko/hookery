*******
hookery
*******

Minimally invasive hooks with no metaclasses and no class decorators since ``v5.0.0``.

Status
======

* ``v3.10.1`` status is ``Beta``.
* ``v5.x`` status is ``Pre-Alpha``.

I use ``v3.10.1`` (https://pypi.org/project/hookery/3.10.1/) in production for work.

This document is for ``v5.x`` which is NOT production-ready yet.


Installation
============

.. code-block:: shell

    pip install hookery==3.10.1

Basic Usage
===========

.. code-block:: python

    from hookery import Hook, hooks

    class Profile:
        on_activated = Hook()

        @on_activated
        def log_activation(self):
            print(f"Activating {self}")

        def activate(self):
            hooks.trigger(self.on_activated)


    class WarehouseProfile(Profile):

        @Profile.on_activated
        def log_activation(self):
            print(f"Warehouse profile {self} is being activated")

        @Profile.on_activated
        def another_handler(self):
            print(f"This will also be printed")


The dummy example above demonstrates that:

* a hook registration requires no metaclasses, no base classes, no class decorators.
* you can register any number of handlers per hook inside the same class
* a handler called ``log_activation`` in child class does not override a handler with the same name
  in parent class.


.. code-block:: python

    >>> profile = WarehouseProfile()
    >>> profile.activate()
    Activating <__main__.WarehouseProfile object at 0x103ee66d8>
    Warehouse profile <__main__.WarehouseProfile object at 0x103ee66d8> is being activated
    This will also be printed


Limitations
===========

* For us, hooks and hook handlers are part of the class specification. This means that a class cannot have new hooks
  added or new hook handlers registered after the class has been created. If you wish to add functionality you either
  modify the class or extend it.
* ``@classmethod``'s and ``@staticmethod``'s cannot be registered as handlers because hooks apply to instances of
  a class, not the class itself.
* It is best to not decorate handlers with anything else.
