#!/usr/bin/env python
import os
from datetime import datetime, timedelta

import pytz

import pizza.services
from pizza import slack
from pizza.models import RSVP
from pizza.utils import getLogger

COMPANY_NAME = os.environ["COMPANY_NAME"]
PIZZA_CHANNEL_ID = os.environ["PIZZA_CHANNEL_SLACK_ID"]
PEOPLE_PER_EVENT = 5
REPLY_DEADLINE_IN_HOURS = 24
DAYS_IN_ADVANCE_TO_INVITE = 10
HOURS_BETWEEN_REMINDERS = 4

BUTTONS_ATTACHMENT = [
    {
        "fallback": "Could not answer :/",
        "callback_id": "rsvp",
        "color": "#3AA3E3",
        "attachment_type": "default",
        "actions": [
            {
                "name": "option",
                "text": "OH YES! :pizza:",
                "type": "button",
                "value": "attending",
            },
            {
                "name": "option",
                "text": "Nah :cry:",
                "type": "button",
                "value": "not attending",
            },
        ],
    }
]

logger = getLogger(__name__)


def invite_if_needed():
    event = pizza.services.get_event_in_need_of_invitations(
        days_in_advance_to_invite=DAYS_IN_ADVANCE_TO_INVITE,
        people_per_event=PEOPLE_PER_EVENT,
    )
    if event is None:
        logger.info("No events in need of invited. No users were invited.")
        return

    number_of_employees = pizza.services.get_number_of_slack_users()
    number_to_invite = PEOPLE_PER_EVENT - pizza.services.get_number_of_invited_users(
        event_id=event.id
    )
    users_to_invite = pizza.services.get_users_to_invite(
        event_id=event.id,
        number_of_users_to_invite=number_to_invite,
        total_number_of_employees=number_of_employees,
        employees_per_event=PEOPLE_PER_EVENT,
    )

    if len(users_to_invite) == 0:
        logger.info(
            "Event in need of users, but noone to invite [event_id=%s]", event.id
        )  # TODO: needs to be handled
        return

    pizza.services.save_invitations(slack_users=users_to_invite, event_id=event.id)

    for slack_user in users_to_invite:
        slack.send_slack_message(
            slack_user.slack_id,
            "You're invited to eat pizza at %s, %s. Please answer within %d hours 🙏. Will you come?"
            % (
                event.location,
                event.time.strftime("%A %d. %B kl %H:%M"),
                REPLY_DEADLINE_IN_HOURS,
            ),
            BUTTONS_ATTACHMENT,
        )
        logger.info(
            "User was invited to event [event_id=%s, user=%s]",
            event.id,
            slack_user.current_username,
        )


def send_reminders():
    invitations = pizza.services.get_unanswered_invitations()

    for invitation in invitations:
        # already reminded
        if invitation.reminded_at:
            continue

        remind_timestamp = invitation.invited_at + timedelta(
            hours=HOURS_BETWEEN_REMINDERS
        )
        if datetime.now(tz=pytz.utc) > remind_timestamp:
            slack.send_slack_message(
                invitation.slack_user_id,
                "Hey! I didn't hear back from you? :sob: Are you up for some pizza? (yes/no)",
            )
            pizza.services.update_reminded_at(slack_id=invitation.slack_user_id)
            logger.info(
                "User reminded about an event [user_id=%s]", invitation.slack_user_id
            )


def finalize_event_if_complete():
    event = pizza.services.get_event_ready_to_finalize(
        people_per_event=PEOPLE_PER_EVENT
    )
    if event is None:
        logger.info("No events ready to finalize")
        return

    slack_ids = [
        "<@%s>" % user.slack_id
        for user in pizza.services.get_attending_users(event_id=event.id)
    ]

    pizza.services.mark_event_as_finalized(event_id=event.id)

    ids_string = ", ".join(slack_ids)
    slack.send_slack_message(
        PIZZA_CHANNEL_ID,
        "Hey folks! :sparkles: %s! You're eating some awesome pizza together at %s, %s. %s books the table, and %s expenses the meal (unless you agree otherwise). Have fun!"
        % (
            ids_string,
            event.location,
            event.time.strftime("%A %d. %B kl %H:%M"),
            slack_ids[0],
            slack_ids[1],
        ),
    )


def auto_reply():
    slack_ids_that_did_not_reply = pizza.services.auto_reply_after_deadline(
        deadline_hours=REPLY_DEADLINE_IN_HOURS
    )
    if not slack_ids_that_did_not_reply:
        return

    for slack_id in slack_ids_that_did_not_reply:
        slack.send_slack_message(
            slack_id,
            "Alright then, I'll assume you can't make it. Crossing my fingers for a more positive response next time! 🤞",
        )
        logger.info(
            "User didn't answer. Setting RSVP to not attending. [slack_id=%s]", slack_id
        )


def rsvp(slack_id: str, answer: RSVP):
    pizza.services.rsvp(slack_id=slack_id, answer=answer)


def get_invited_users():
    return pizza.services.get_invited_users()


def sync_db_with_slack() -> None:
    slack_users = slack.get_real_users(slack.get_slack_users())
    pizza.services.update_slack_users(slack_users=slack_users)
