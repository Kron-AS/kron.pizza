#!/usr/bin/env python

from pizza import api
from pizza.utils import getLogger, tz_aware_now

logger = getLogger(__name__)


def main():
    # Don't do anything in the evening/night
    current_hour = tz_aware_now().hour
    if current_hour >= 20 or current_hour < 8:
        logger.info(
            "Current hour %d is not during «business hours» so not doing anything",
            current_hour,
        )
        return

    api.sync_db_with_slack()
    api.auto_reply()
    api.invite_if_needed()
    api.send_reminders()
    api.finalize_event_if_complete()


if __name__ == "__main__":
    main()
