import argparse

import pytest

from hookery.v4 import Hook, HookSpec


class CliHooks(HookSpec):
    init_parser = Hook()
    inject_args = Hook()
    get_plugins = Hook()


cli_hooks = CliHooks()


class DateLimitMixin:
    date_range = None

    @cli_hooks
    def init_parser(self, parser):
        parser.add_argument('--date-from')
        parser.add_argument('--date-to')

    @cli_hooks
    def inject_args(self, args):
        if args.date_from or args.date_to:
            self.date_range = (args.date_from, args.date_to)


class CountLimiMixin:
    limit_count = None

    @cli_hooks
    def init_parser(self, parser):
        parser.add_argument('--count', type=int)

    @cli_hooks
    def inject_args(self, args):
        self.limit_count = args.count


class Cli:
    def run(self, args=None):
        parser = argparse.ArgumentParser()
        cli_hooks.init_parser.trigger(self, parser=parser)

        args = parser.parse_args(args=args)
        cli_hooks.inject_args.trigger(self, args=args)


class FirstCli(DateLimitMixin, CountLimiMixin, Cli):
    @cli_hooks
    def init_parser(self, parser):
        parser.add_argument('--my-first-argument')


class SecondCli(DateLimitMixin, CountLimiMixin, Cli):
    @cli_hooks
    def init_parser(self, parser):
        parser.add_argument('--my-second-argument')


def test_first_cli(capsys):
    with pytest.raises(SystemExit):
        FirstCli().run(args=['--help'])

    out, err = capsys.readouterr()
    assert '--date-from DATE_FROM' in out
    assert '--count COUNT' in out
    assert '--my-first-argument MY_FIRST_ARGUMENT' in out
    assert '--my-second-argument' not in out


def test_second_cli(capsys):
    with pytest.raises(SystemExit):
        SecondCli().run(args=['--help'])

    out, err = capsys.readouterr()
    assert '--date-from DATE_FROM' in out
    assert '--count COUNT' in out
    assert '--my-first-argument' not in out
    assert '--my-second-argument MY_SECOND_ARGUMENT' in out
