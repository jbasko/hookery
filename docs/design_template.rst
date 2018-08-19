######
HDP 00
######

==========
Main Ideas
==========

* Describe which previous HDP this is based on.
* Describe what changes are you experimenting with.

===========
Main Issues
===========

* Write conclusions here.

===
API
===

----------------
Hook Declaration
----------------

Declare a hook called ``on_activated`` for class ``Profile`` and trigger its handlers from
method ``activate()``:

.. code-block:: python

    class Profile:

        # TODO declare the on_activated hook

        def activate():
            # TODO trigger the handlers of on_activated hook


Discussion
""""""""""

* Discuss implications of the design proposed above.

-------------------------------
Class Hook Handler Registration
-------------------------------

Register two handlers for the ``on_activated`` hook inside ``Profile`` class:

.. code-block:: python

    class Profile:

        # .. hook declaration code skipped ..

        # TODO register this method as a hook
        def log_activation(self):
            print(f"Activating {self}")

        # TODO register this method as a hook
        def validate_activation(self):
            print(f"Validating activation of {self}")

        def activate():
            # .. hook trigger code skipped ..
            pass


Discussion
""""""""""

* Discuss implications of the design proposed above.


--------------------------------------------
Class Hook Handler Registration in Sub-Class
--------------------------------------------

Create class ``CustomProfile`` which inherits from ``Profile``. This class should register
a handler method ``log_activation`` which must not affect
method of the same name registered in ``Profile`` class body as ``Profile.on_activated`` handler:

.. code-block:: python

    class CustomProfile(Profile):

        # TODO register this method as a hook fo Profile.on_activated
        def log_activation(self):
            print(f"Activating CUSTOM {self}")


Discussion
""""""""""

* Discuss implications of the design proposed above.

-----------------------------
Hook Declaration in Sub-Class
-----------------------------

Add a hook specific to the derived ``CustomProfile`` class -- ``on_customisation`` and register a
single handler for it:

.. code-block:: python

    class CustomProfile(Profile):

        # .. code skipped ..

        # TODO declare hook "on_customisation"

        # TODO register this method as a handler for "on_customisation"
        def log_customisation(self):
            print(f"Customising {self}")


Discussion
""""""""""

* Discuss implications of the design proposed above.

----------------------------------
Instance Hook Handler Registration
----------------------------------

Given ``p``, an instance of ``Profile``, how do I register a handler for ``on_activated`` which will be called only
when this particular instance is being activated?

.. code-block:: python

    master = Profile()

    def on_master_profile_activated(profile):
        print(f"Activating master profile {profile}")

    # TODO Register on_master_profile_activated as Profile.on_activated handler for master only.


Discussion
""""""""""

* Discuss implications of the design proposed above.

-----------------------
Hook Handler Inspection
-----------------------

Handler inspection. Print a list of all registered handlers for a given hook with respect to the class, or a concrete
instance:

.. code-block:: python

    class Profile:
        # .. code skipped ..
        pass

    class CustomProfile(Profile):
        # .. code skipped ..
        pass

    # TODO List on_activated handlers associated with all Profile instances

    # TODO List on_activated handlers associated with all CustomProfile instances

    p = Profile()
    # TODO List on_activated handlers associated with p

    c = CustomProfile()
    # TODO List on_activated handlers associated with c


Discussion
""""""""""

* Discuss implications of the design proposed above.

=========
Questions
=========

* Where are the registered class hook handlers stored?

* Where are the registered instance hook handlers stored?

* All hook handlers are instance methods. How is the first argument of these methods, ``self``, reliably populated
  from wherever the hook is triggered?

* What happens when user creates a new class ``CustomProfile`` which inherits from class ``Profile``
  and in the new class declares method with the same name as a hook declared in its parent class -- ``on_activated``?

* What is returned by ``Profile.on_activated``?

* What is returned by ``CustomProfile.on_activated``?

* What happens when ``Profile.on_activated()`` is called from outside ``Profile`` body?

* What happens when ``CustomProfile.on_activated()`` is called from outside ``CustomProfile`` body?

* What happens when ``Profile().on_activated()`` is called?

* What happens when ``CustomProfile().on_activated()`` is called?

* What happens to all of the above when class ``CombinedProfile`` inherits from
  ``FirstProfile`` and ``SecondProfile`` both of which inherit from ``Profile``?

* How to list all hooks available for a given class?
