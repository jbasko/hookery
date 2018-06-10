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


class CountLimitMixin:
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


class FirstCli(DateLimitMixin, CountLimitMixin, Cli):
    @cli_hooks
    def init_parser(self, parser):
        parser.add_argument('--my-first-argument')


class SecondCli(DateLimitMixin, CountLimitMixin, Cli):
    @cli_hooks
    def init_parser(self, parser):
        parser.add_argument('--my-second-argument')


def test_first_cli_init():
    cli = FirstCli()
    handlers = cli_hooks.get_handlers('init_parser', cli)
    assert handlers == [
        CountLimitMixin.init_parser,
        DateLimitMixin.init_parser,
        FirstCli.init_parser,
    ]


def test_first_cli_runs(capsys):
    with pytest.raises(SystemExit):
        FirstCli().run(args=['--help'])

    out, err = capsys.readouterr()
    assert '--my-first-argument' in out
    assert '--my-second-argument' not in out


def test_second_cli_init():
    cli = SecondCli()
    handlers = cli_hooks.get_handlers('init_parser', cli)
    assert handlers == [
        CountLimitMixin.init_parser,
        DateLimitMixin.init_parser,
        SecondCli.init_parser,
    ]


def test_second_cli_runs(capsys):
    with pytest.raises(SystemExit):
        SecondCli().run(args=['--help'])

    out, err = capsys.readouterr()

    assert '--my-first-argument' not in out
    assert '--my-second-argument' in out


def test_can_register_instance_specific_handler():
    cli1 = FirstCli()
    cli2 = FirstCli()

    @cli_hooks.init_parser(cli1)
    def init_parser(parser):
        parser.add_argument('--dry-run', action='store_true')

    assert len(cli_hooks.get_handlers('init_parser', cli1)) == 4
    assert len(cli_hooks.get_handlers('init_parser', cli2)) == 3
