#!/usr/bin/env python

import os

from slack import WebClient

slack_token = os.environ["SLACK_API_TOKEN"]
sc = WebClient(token=slack_token)


def get_slack_users():
    return sc.users_list()["members"]


def get_real_users(all_users):
    return [
        u
        for u in all_users
        if not u["deleted"]
        and not u["is_bot"]
        and not u["is_restricted"]
        and not u["name"] == "slackbot"
    ]


def send_slack_message(channel_id, text, attachments=None, thread_ts=None):
    return sc.chat_postMessage(
        channel=channel_id,
        as_user=True,
        text=text,
        attachments=attachments,
        thread_ts=thread_ts,
    )
