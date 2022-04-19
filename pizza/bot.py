#!/usr/bin/env python
import logging
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from pizza import api, slack

logging.basicConfig(level=logging.INFO)

app = App(token=os.environ["SLACK_BOT_TOKEN"])


@app.event("message")
def on_message(message, say, logger):
    logger.info("Received message [payload=%s]", message)

    if not message["channel_type"] == "im":
        logger.info("Ignoring non-IM message")
        return

    if "subtype" in message:
        logger.info(
            "Ignoring message as it has a subtype [subtype=%s]", message["subtype"]
        )
        return

    if not message["user"] in api.get_invited_users():
        logger.info(
            "Ignoring message, could not find invited user [user=%s]", message["user"]
        )
        slack.send_slack_message(
            message["channel"],
            "Hehe, I'm just a stupid robot and don't understand what you want. No pizza events planned at the moment? 😳",
        )
        return

    if message["text"].lower() == "yes":
        api.rsvp(message["user"], "attending")
        slack.send_slack_message(message["channel"], "Sweet! 🤙")
        api.finalize_event_if_complete()

    elif message["text"].lower() == "no":
        api.rsvp(message["user"], "not attending")
        slack.send_slack_message(message["channel"], "Ok 😏")
        api.invite_if_needed()

    else:
        slack.send_slack_message(
            message["channel"],
            "Hehe I'm just a stupid robot and I don't understand what you mean 😳. Can you attend? (yes/no)",
        )


@app.action("rsvp")
def handle_rsvp(ack, body, say, respond, logger):
    ack()

    logger.info("Received action [payload=%s]", body)

    user_id = body["user"]["id"]

    if user_id not in api.get_invited_users():
        say(
            "💣 Hmm, this is weird.. Something is wrong (you're not invited to any events) and I don't know what to do."
        )
        return

    for action in body["actions"]:
        rsvp = action["value"]

        api.rsvp(user_id, rsvp)
        if rsvp == "attending":
            logger.info("User is attending event [user=%s]", user_id)
            api.finalize_event_if_complete()
            respond("✅ Sweet! It'll be awesome! 😋", replace_original=False)
        elif rsvp == "not attending":
            logger.info("User is *not* attending event [user=%s]", user_id)
            api.invite_if_needed()
            respond("⛔️ Ah, ok. Next time! 🤝", replace_original=False)


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
