#!/usr/bin/env python

from pizza import api

api.sync_db_with_slack()
api.auto_reply()
api.invite_if_needed()
api.send_reminders()
