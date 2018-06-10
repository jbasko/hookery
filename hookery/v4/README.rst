##################
hookery, version 4
##################


*********************************************************
Example 1: Command-Line Interface Composition from Mixins
*********************************************************

.. code-block:: python

    import argparse

    from hookery.v4 import HookSpec, Hook


    class CliHooks(HookSpec):
        init_parser = Hook()
        inject_args = Hook()


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


    cli = SecondCli().run(['--help'])

