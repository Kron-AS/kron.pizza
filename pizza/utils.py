import functools
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import pythonjsonlogger.jsonlogger

DEFAULT_TIME_ZONE = ZoneInfo("Europe/Oslo")


@functools.lru_cache
def setup_logging():
    _json_formatter = pythonjsonlogger.jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(message)s %(pathname)s %(name)s %(threadName)s %(funcName)s %(levelno)s %(lineno)s"
    )
    _console_handler = logging.StreamHandler(sys.stdout)
    _console_handler.setFormatter(_json_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(_console_handler)


def getLogger(name):
    _ = setup_logging()
    return logging.getLogger(name)


def tz_aware_now(*, tz: ZoneInfo = DEFAULT_TIME_ZONE) -> datetime:
    return datetime.now(tz=tz)


def strtobool(val):
    """
    Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    elif val in ("n", "no", "f", "false", "off", "0"):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))
