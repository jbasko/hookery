import argparse

from hookery.v4 import HookSpec, Hook


class CliHooks(HookSpec):
    init_parser = Hook()
    inject_args = Hook()


cli_hooks = CliHooks()


@cli_hooks.init_parser
def log_level(parser):
    parser.add_argument('--log-level')



# TODO Should we support also @CliHooks.init_parser??
# TODO The idea would be to register init_parser for all instances of CliHooks ...
# TODO That's what hookery3 does, no?


def run_cli():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda: None)
    cli_hooks.init_parser.trigger(parser=parser)
    args = parser.parse_args()
    cli_hooks.inject_args.trigger(parser=parser, args=args)
    args.func()


if __name__ == '__main__':
    run_cli()
