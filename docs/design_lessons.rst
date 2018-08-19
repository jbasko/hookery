##############
Design Lessons
##############


----------------------------
Inheriting from ``Hookable``
----------------------------

If we are doing the instance methods interface, we must either inherit from some parent class which has a custom
metaclass or we must require a class decorator which would make the class actually do the same thing. This is because
we need to be in control of the class creation.

With global functions interface this is most likely not required.
Probably everything can be achieved with descriptors but must be careful about attributes backed by descriptors
not being auto-initialised.

-------------------------------------------------------
No Class Hook Handler Registration After Class Creation
-------------------------------------------------------

After a hookable class (sub-class of ``Hookable``) has been created, no handlers for the hooks of that class
should be registered. Handlers are key functionality of the class.
Hook handlers belong to the declaration of the class.
Ability to change them after the creation of the class makes it harder to think about what the class actually does.
If user needs to modify the behaviour of all instances of a class, they should extend the class and use the sub-class.
If user needs to modify the behaviour of a particular instance, they should register a handler for that particular
instance.

This also means that calling anything like ``Profile.on_activation`` (or ``Profile.Hooks.on_activation`` and
other variants) with a function as an argument should return a temporary object, but should not register the handler
in class ``Profile``.
