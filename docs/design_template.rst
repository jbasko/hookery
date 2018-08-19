#######
HDP 000
#######

Declare a hook called ``on_activated`` for class ``Profile`` and trigger its handlers from
method ``activate()``:

.. code-block:: python

    class Profile:

        # TODO declare the on_activated hook

        def activate():
            # TODO trigger the handlers of on_activated hook


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
