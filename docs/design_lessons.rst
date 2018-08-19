##############
Design Lessons
##############


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
