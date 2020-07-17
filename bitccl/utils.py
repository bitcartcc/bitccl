import importlib
import inspect
import json
import os
import signal
import traceback
from contextlib import contextmanager

from . import events
from .datatypes import ExtendedDict
from .exceptions import TimeoutException
from .logger import logger


def load_config():
    config = {}
    data = ""
    if not os.path.exists("config.json"):
        logger.debug(
            "No config file existing. No settings set. Some functions might not work properly"
        )
    try:
        with open("config.json") as f:
            data = f.read()
    except OSError:
        logger.debug("Error reading config file")
    try:
        config = json.loads(data)
    except json.JSONDecodeError:
        logger.debug("Invalid json in config file")
    return ExtendedDict(lambda: None, **config)


def silent_debug():
    caller_name = inspect.currentframe().f_back.f_code.co_name
    logger.debug(f"Error in {caller_name}. Traceback:\n{traceback.format_exc()}")


def no_imports_importer(*args, **kwargs):
    raise ImportError("Imports disabled")


def allow_imports(func):
    def wrapper(*args, **kwargs):
        __builtins__["__import__"] = importlib.__import__
        result = func(*args, **kwargs)
        __builtins__["__import__"] = no_imports_importer
        return result

    return wrapper


def prepare_event(event):
    if isinstance(event, str):
        event = getattr(events, event, events.BaseEvent)()
    if inspect.isclass(event) and issubclass(event, events.BaseEvent):
        event = event()
    return event


def init_base_event():
    events.BaseEvent.init_imports()


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)