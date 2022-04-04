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
