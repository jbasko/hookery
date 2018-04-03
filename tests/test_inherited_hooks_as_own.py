from hookery import InstanceHook, hookable
from hookery.base import Hookable


def test_direct_descendant():
    @hookable
    class Field:
        parser = InstanceHook(single_handler=True)

    class Integer(Field):

        # The parser is registered against parent class's hook because the current class's hook
        # is not available yet in class's body.
        @Field.parser
        def parse(self, value):
            return int(value)

    assert isinstance(Integer(), Hookable)

    assert not Field.parser
    assert Integer.parser

    assert not Field().parser
    assert Integer().parser

    assert Integer().parser.trigger(value='55') == 55


def test_further_descendant():
    @hookable
    class Field:
        parser = InstanceHook(single_handler=True)

    class Integer(Field):
        @Field.parser
        def parser1(self, value):
            return int(value)

    class BetterInteger(Integer):
        pass

    class PositiveInteger(BetterInteger):
        @Integer.parser
        def parser2(self, value):
            return abs(int(value))

    assert not Field.parser

    assert Integer.parser
    assert Integer().parser.trigger(value='-55') == -55

    assert PositiveInteger.parser
    assert PositiveInteger().parser.trigger(value='-55') == 55
