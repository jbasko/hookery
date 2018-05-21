*******
hookery
*******

.. code-block:: shell

    pip install hookery

*hookery* is to be used when inheritance becomes too complicated and it is easier to extend
functionality by registering hook handlers instead of overriding parent class methods.

Works with Python 3.5+ and will not work with anything older.

Example
-------

This demonstrates a hookable class ``Field`` with one hook ``mapper`` which can be used to customise
mapping of a field from a source dictionary to a target dictionary.

If someone wants to extend the functionality of ``Field`` class they would either register handlers
on concrete instances of ``Field`` like ``validate_height`` which is registered with ``height`` field,
or with classes like ``Field.default_mapper``, ``source_printer``, and ``Integer.to_int``.

.. code-block:: python

    from hookery import hookable, InstanceHook


    @hookable
    class Field:
        mapper = InstanceHook(args=('field', 'source', 'target'))

        @mapper
        def default_mapper(self, source, target):
            target[self.name] = source.get(self.name, None)

        def __init__(self, name):
            self.name = name

        def map(self, source, target=None):
            if target is None:
                target = {}
            self.mapper.trigger(field=self, source=source, target=target)
            return target


    @Field.mapper
    def source_printer(source):
        print('source:', source)


    class Integer(Field):

        @Field.mapper
        def to_int(self, target):
            target[self.name] = int(target[self.name]) if target[self.name] is not None else None


    height = Integer('height')


    @height.mapper
    def validate_height(field, target):
        if target[field.name] > 250:
            raise ValueError((field.name, target[field.name]))

    print(height.map({'height': '165'}))


----

Introduction
------------


A **hookable** is something that one can hook into (onto, around, or about) using **hooks**.
This something is usually an algorithm, a strategy of some sort;
and hooks are points in the execution of this strategy at which the designer of the strategy
allows user to monitor the execution of the strategy or to change it.

To hook into a strategy, user picks one of the hooks the strategy exposes and registers a **handler** for it.
A handler is just a function. A hook may have zero, one or multiple handlers registered with it.
When a hookable strategy is executed and the control of the program reaches a hooking point,
the corresponding hook will be **triggered**, and through that all registered handler functions
will be called and their results collected.

*hookery* provides a few flavours of hooks: **standalone hooks**, **class hooks**, and **instance hooks**.

**A standalone hook** is just something that can be registered handlers with. It does not have a subject,
it is not associated with any class or instance and so it does not inherit any handlers. All handlers
are registered directly on the hook object itself.

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

Any class can be marked as hookable either by decorating it with ``@hookable`` decorator, extending ``Hookable``, or
setting its metaclass to ``HookableMeta``.

The recommended method is the ``@hookable`` decorator.

Classes derived from a hookable class are also hookable.

.. code-block:: python

    @hookable
    class Request:
        before = InstanceHook()
        after = InstanceHook()

Single-Handler Hooks
--------------------

A single-handler hook is a hook for which only the last registered handler matters.
By default, a hook can have an unlimited number of handlers, and results from all of them will be collected
when the hook is triggered. The results are then returned as a list. But for a single-handler hook, ``trigger()``
will only call the last handler and return result as is. If there is no handler registered, ``None`` will be returned.

If the majority of your hooks are single-handler hooks instance hooks for which you register handlers in class
body then you are probably misusing hooks. A single-handler hook in such scenario is clearer to express
as a just a normal instance method. Hooks are simpler to use than methods if handlers need to be attached directly
to instances.


Handlers
--------

Any function or generator function can be registered as a handler.

If a handler is a generator function, it will be fully consumed on hook trigger and all the values
it yields will be returned as a list. To disable this functionality, the hook must be declared
with ``consume_generators=False``.

.. code-block:: python

    on_application_shutdown = Hook()

    @on_application_shutdown
    def say_bye(user):
        print('Bye {}!'.format(user))

Handlers can specify arguments they expect and they don't have to match the arguments with which
the hook is triggered -- only the requested arguments will be supplied.

.. code-block:: python

    on_application_shutdown.trigger(greeting='Good bye {}', user='M. A.')

Functions decorated with ``@classmethod`` and ``@staticmethod`` cannot be registered as handlers.

----


Feature Markers in Code
-----------------------

There are some features which are hard to explain without an example and which require handling in multiple
places in code and documenting each place with an example would be a nightmare.
Instead we use the following markers to decode which feature is being implemented.

**[H001]**

Even though ``on_before`` is decorated with ``@Request.before``, the handler is registered
only with ``SafeRequest.before``.

.. code-block:: python

    @hookable
    class Request:
        before = InstanceHook()


    class SafeRequest(Request)
        @Request.before
        def on_before():
            pass

**[H002]**

.. code-block:: python

    @hookable
    class Field:
        parser = InstanceHook()

        @parser
        def parse_value(self, value):
            return int(value)

If a hook is declared in the same class body in which it is used to register a handler, then
we need to take special care as ``parser`` is not associated with the containing ``Field`` class yet.

