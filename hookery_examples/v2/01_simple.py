from hookery import Registry

hooks = Registry()

sun_rises = hooks.register_event('sun_rises')
sun_sets = hooks.register_event('sun_sets')


@sun_rises.listener
def say_good_morning():
    print('Good morning!')


@sun_rises.listener
def say_correct_time():
    import datetime
    print('Current time is {}'.format(datetime.datetime.utcnow().isoformat()))


@sun_sets.listener
def say_good_night():
    print('Good night!')


def main():
    sun_rises()
    sun_sets()


if __name__ == '__main__':
    main()
