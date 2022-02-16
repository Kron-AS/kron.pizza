#!/usr/bin/env python

import os
import sys
from time import sleep

from slackclient import SlackClient

from pizza import api

slack_token = os.environ["SLACK_API_TOKEN"]

sc = SlackClient(slack_token)


def is_dm(message):
    return message["channel"][0] == "D"


if not sc.rtm_connect():
    print("Connection Failed, invalid token?")
    sys.exit(1)


def main():
    while True:
        event_list = sc.rtm_read()
        message_list = list(filter(lambda m: m["type"] == "message", event_list))
        for message in message_list:
            if is_dm(message) and "user" in message:
                if message["user"] in api.get_invited_users():
                    if message["text"].lower() == "ja":
                        api.rsvp(message["user"], "attending")
                        api.send_slack_message(message["channel"], "Sweet! 🤙")
                        api.finalize_event_if_complete()
                    elif message["text"].lower() == "nei":
                        api.rsvp(message["user"], "not attending")
                        api.send_slack_message(message["channel"], "Ok 😏")
                        api.invite_if_needed()
                    else:
                        api.send_slack_message(
                            message["channel"],
                            "Hehe jeg er litt dum, jeg. Skjønner jeg ikke helt hva du mener 😳. Kan du være med? (ja/nei)",
                        )
        sleep(0.5)


if __name__ == "__main__":
    main()
