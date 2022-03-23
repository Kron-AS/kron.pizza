from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_TIME_ZONE = ZoneInfo("Europe/Oslo")


def tz_aware_now(*, tz: ZoneInfo = DEFAULT_TIME_ZONE) -> datetime:
    return datetime.now(tz=tz)
