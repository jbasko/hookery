++++++++++++
Introduction
++++++++++++

A instance of a class extending :class:`~hookery.v4.base.HookSpec` serves as a hook specification. It is used, both,
to register hook handlers and to store them. Hook handlers are registered against a context in which
they apply.

.. literalinclude:: ../../tests/v4_tests/test_cli_hooks_example.py
    :language: python
    :lines: 1-12

Given an instance ``cli_hooks`` of a class ``CliHook`` (which extends :class:`~hookery.v4.base.HookSpec`), there are
two ways we can register handlers against hooks specified in ``cli_hooks``:

1. By using ``@cli_hooks`` decorator
2. By using ``@cli_hooks.<hook_name>`` decorator, for example, ``@cli_hooks.init_parser``.

Here, we register a simple function as a handler:

.. literalinclude:: ../../tests/v4_tests/test_cli_hooks_example.py
    :language: python
    :lines: 13-17

