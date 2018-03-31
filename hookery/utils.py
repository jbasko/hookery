import functools
import inspect


def optional_args_func(func) -> callable:
    """
    Given a function or generator `func`, return a function/generator
    that takes any number of kwargs and calls `func` with only the args/kwargs
    that `func` expects.
    """
    if getattr(func, '_optional_args_func', False):
        return func

    is_generator = inspect.isgeneratorfunction(func)
    func_sig = inspect.signature(func)
    expects_nothing = not func_sig.parameters

    if is_generator:
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            if expects_nothing:
                yield from func()
            else:
                bound_arguments = func_sig.bind(*args, **{k: v for k, v in kwargs.items() if k in func_sig.parameters})
                yield from func(*bound_arguments.args, **bound_arguments.kwargs)
    else:
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            if expects_nothing:
                return func()
            else:
                bound_arguments = func_sig.bind(*args, **{k: v for k, v in kwargs.items() if k in func_sig.parameters})
                return func(*bound_arguments.args, **bound_arguments.kwargs)

    # Mark it so that we don't double wrap our own
    setattr(wrapped, '_optional_args_func', True)

    return wrapped
