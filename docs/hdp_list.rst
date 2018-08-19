===============================
Hookery Design Proposals (HDPs)
===============================

------
HDP-01
------


------
HDP-02
------


------
HDP-03
------

Global functions style.



.. code-block:: python

    class Profile:

        on_activated = Hook()

        @on_activated
        def log_activation(self):
            print(f"Activating {self}")

        def activate(self):
            hooks.trigger(self.on_activated, *args, **kwargs)