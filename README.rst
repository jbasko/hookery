*******
hookery
*******

It's really simple. There are some events in the lifetime of your simple Python application that you want to hook into,
and you don't want to be overriding methods or writing conditional code to do that. What you do is you
introduce hooks and register callbacks.

.. code-block:: python

    from hookery import HookRegistry

    hooks = HookRegistry()
    hooks.user_added = hooks.create_hook('user_added')

    _users = {}


    def create_user(username, password):
        _users[username] = password
        hooks.handle(hooks.user_added, username=username)


    @hooks.user_added
    def notify_me():
        print('A new user has been added!')


    @hooks.user_added
    def say_hi(username):
        print('Hi, {}'.format(username))


.. code-block:: python

    >>> create_user('Bob', password='secret')
    A new user has been added!
    Hi, Bob

