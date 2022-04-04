#!/usr/bin/env python
import functools
import os

from slack_sdk.web import WebClient

from pizza.utils import getLogger

slack_token = os.environ["SLACK_BOT_TOKEN"]
debug = os.environ.get("DEBUG", False)
logger = getLogger(__name__)


@functools.cache
def slack_client():
    return WebClient(token=slack_token)


def get_slack_users():
    sc = slack_client()
    return sc.users_list()["members"]


def get_real_users(all_users):
    return [
        u
        for u in all_users
        if not any(
            (
                u.get("deleted", False),
                u.get("is_bot", False),
                u.get("is_restricted", False),
                u.get("is_ultra_restricted", False),
                u["name"] == "slackbot",
            )
        )
    ]


def send_slack_message(channel_id, text, attachments=None, thread_ts=None):
    if debug:
        logger.info(
            "Slack message not sent due to debug [channel_id=%s, msg=%r]",
            channel_id,
            text,
        )
        return

    # TODO: enable when safe
    # sc = slack_client()
    # return sc.chat_postMessage(
    #     channel=channel_id,
    #     as_user=True,
    #     text=text,
    #     attachments=attachments,
    #     thread_ts=thread_ts,
    # )
