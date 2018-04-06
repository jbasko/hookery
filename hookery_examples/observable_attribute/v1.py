from hookery import InstanceHook, hookable


class ObservableAttr:
    def __init__(self, name=None, default=None):
        self.name = name
        self.default = default

    @property
    def attr_store_name(self):
        return '_observableattr#{}'.format(self.name)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if not hasattr(instance, self.attr_store_name):
            setattr(instance, self.attr_store_name, self.default)
        return getattr(instance, self.attr_store_name)

    def __set__(self, instance, value):
        setattr(instance, self.attr_store_name, value)
        instance.updated.trigger(self=instance)


@hookable
class Address:
    updated = InstanceHook()

    city = ObservableAttr('city')
    country = ObservableAttr('country')


address = Address()
address.city = 'London'
address.country = 'UK'


@address.updated
def check_city(self):
    if self.city != 'London':
        print('Why are you not in London?')


address.city = 'Guildford'
