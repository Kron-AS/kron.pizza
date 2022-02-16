#!/usr/bin/env python

import json

import requests
from flask import Flask, request

from pizza import api

app = Flask(__name__)


@app.route("/api/action", methods=["GET", "POST"])
def action():
    if not request.form.get("payload"):
        return "Payload not provided", 400

    payload = json.loads(request.form.get("payload"))
    responses = []
    response_url = payload["response_url"]

    for action in payload["actions"]:
        responses.append(
            button_rsvp(
                payload["user"]["id"],
                action["value"],
                payload["original_message"],
                response_url,
            )
        )

    return "", 200


def button_rsvp(user_id, rsvp, original_message, response_url):
    if user_id in api.get_invited_users():
        api.rsvp(user_id, rsvp)
        if rsvp == "attending":
            api.finalize_event_if_complete()
            response_JSON = response_message(
                original_message, "✅ Sweet! Det blir sykt nice! 😋"
            )
            requests.post(response_url, response_JSON)
        elif rsvp == "not attending":
            api.invite_if_needed()
            response_JSON = response_message(
                original_message, "⛔️ Ah, ok. Neste gang! 🤝"
            )
            requests.post(response_url, response_JSON)
    else:
        response_JSON = response_message(
            original_message, "💣 Hmm, hva har du gjort for noe rart nå?"
        )
        requests.post(response_url, response_JSON)


def response_message(original_message, text):
    original_message["attachments"] = [{"text": text}]
    return json.dumps(original_message)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
