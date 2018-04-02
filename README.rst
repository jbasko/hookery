*******
hookery
*******

Trivial, primitive, naive, and optimistic hooks in Python 3.5+.

.. code-block:: shell

    pip install hookery


A **hookable** is something that one can hook into (onto, around, or about) using **hooks**.
This something is usually an algorithm, a strategy of some sort;
and hooks are points in the execution of this strategy at which the designer of the strategy
allows user to monitor the execution of the strategy or to change it.

To hook into a strategy, user picks one of the hooks the strategy exposes and registers a **handler** for it.
A handler is just a function. A hook may have zero, one or multiple handlers registered with it.
When a hookable strategy is executed and the control of the program reaches a hooking point,
the corresponding hook will be **triggered**, and through that all registered handler functions
will be called and their results collected.

*hookery* provides a few flavours of hooks: **global hooks**, **class hooks**, and **instance hooks**.

**Global hooks** are the simplest -— they are just events in global scope that user
can subscribe to (register handlers with) and can trigger from anywhere without any context.
They don’t necessarily have to be global, but they are unless user manages the scope.
For example, if your application had a global ``before_shutdown`` hook
then handlers registered with it would be called for all applications.

**A class hook** is associated with a particular class. By default, a separate hook is generated
automatically for every class derived from this class, however, the derived class hook inherits
all handlers registered with the parent class's corresponding hook. Attempt to trigger a class hook
from an instance of the class raises ``TypeError``. Class hooks are just hooks that use class they belong
to as a namespace. When you create a new class with a hookable class as its base class, the new class
will inherit all the handlers registered with hooks of the parent class.

**An instance hook** is also associated with a hookable class, but a separate instance-associated hook is
auto-generated for each instance of this class. That way handlers can be registered separately with the
class-associated hook (to affect all instances of the class) and with the instance-associated hook
(to only affect the particular instance). Unlike with class hooks which are triggered against a particular
class, an instance hook can only be triggered with a particular instance in context, triggering such hook
on class will raise a ``TypeError``. When such hook is triggered, all handlers registered
with the class-associated hook will be called first and then all handlers for the instance-associated hook
will be called.

Hookable Class
--------------

Any class can be marked as hookable by decorating it with ``@hookable`` decorator. The decorator itself
doesn't do anything unless the class declares, as class attributes, some hooks (instances of ``Hook``).

Classes derived from a hookable class are hookable too, but only as long as they don't declare
any new hooks. If a derived class declares a hook, the derived class must also be decorated with ``@hookable``
for the new hooks to be initialised properly.


Single-Handler Hooks
--------------------

A single-handler hook is a hook for which only the last registered handler matters.
By default, a hook can have an unlimited number of handlers, and results from all of them will be collected
when the hook is triggered. The results are then returned as a list. But for a single-handler hook, ``trigger()``
will only call the last handler and return result as is. If there is no handler registered, ``None`` will be returned.


Handlers
--------

Any function or generator function can be registered as a handler.

If a handler is a generator function, it will be fully consumed on hook trigger and all the values
it yields will be returned as a list.

Functions decorated with ``@classmethod`` and ``@staticmethod`` cannot be registered as handlers.
