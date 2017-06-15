*******
hookery
*******

.. code-block:: shell

    pip install hookery


It's really simple. There are some events in the lifetime of your simple Python application that you want to hook into,
and you don't want to be overriding methods or writing conditional code to do that. What you do is you
introduce events and register hooks.


.. code-block:: python

    from hookery import HookRegistry

    hooks = HookRegistry()

    # It doesn't matter where you put the event instance.
    # We set it as a hooks attribute just to keep things tidy
    # in this module.
    hooks.user_added = hooks.register_event('user_added')

    # A dummy user storage
    _users = {}


    def create_user(username, password):
        _users[username] = password
        hooks.user_added.trigger(username=username)


    @hooks.user_added
    def notify_me():
        print('A new user has been added!')


    @hooks.user_added
    def say_hi(username):
        print('Hi, {}'.format(username))

Now you can *create* some users and let all listeners know about it:

.. code-block:: python

    >>> create_user('Bob', password='secret')
    A new user has been added!
    Hi, Bob
