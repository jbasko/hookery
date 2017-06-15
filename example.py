from hookery import HookRegistry

hooks = HookRegistry()

# It doesn't matter where you put the event instance.
# We set it as a hooks attribute just to keep things tidy
# in this module.
hooks.user_added = hooks.register_event('user_added')

_users = {}


def create_user(username, password):
    # A dummy user storage
    _users[username] = password
    hooks.user_added.trigger(username=username)


@hooks.user_added
def notify_me():
    print('A new user has been added!')


@hooks.user_added
def say_hi(username):
    print('Hi, {}'.format(username))


create_user('Bob', password='secret')
