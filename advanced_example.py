"""
This demonstrates that hookery allows to hook into itself too:
you can hook into "hook_registered" event to be notified when someone registers a hook on any event!
"""

from hookery import HookRegistry

hooks = HookRegistry()


@hooks.hook_registered
def hook_registered(event, hook):
    print('{!r} wants to listen to {}'.format(hook, event.name))


on_christmas = hooks.register_event('on_christmas')
on_easter = hooks.register_event('on_easter')


@on_christmas
def send_xmas_greeting():
    print('Merry Christmas!')


@on_easter
def send_easter_greeting():
    print('Happy Easter!')

