import inspect
import logging


def get_caller_name():
    stack = inspect.stack()
    if len(stack) < 3:
        return 'No caller found'
    caller_frame = stack[2]
    caller_name = caller_frame.function
    return caller_name


def logi(*args, message=None, label=None, **kwargs, ):
    if message is None:
        if label is None:
            label = get_caller_name()
        message = label + ": %s"
    else:
        if '%s' not in message:
            message += ': %s'
    if args:
        content = args
    else:
        content = kwargs
    logging.info(message, content)
