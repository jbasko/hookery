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


create_user('Bob', password='secret')

