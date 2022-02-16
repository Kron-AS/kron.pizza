#!/usr/bin/env python

import os

from slackclient import RTMClient

from pizza import api


@RTMClient.run_on(event='message.im')
def on_message(**payload):
    message = payload['data']
    if not message["user"] in api.get_invited_users():
        return

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


if __name__ == "__main__":
    rtm_client = RTMClient(token=os.environ["SLACK_API_TOKEN"])
    rtm_client.start()
