import math
from datetime import timedelta
from typing import Any, Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert

from pizza.db import session
from pizza.models import RSVP, Event, Invitation, SlackUser
from pizza.utils import tz_aware_now


def update_slack_users(*, slack_users: list[Any]):
    data = [
        {
            "slack_id": u["id"],
            "current_username": u["name"],
            "email": u["profile"]["email"],
        }
        for u in slack_users
    ]

    with session() as db:
        insert_stmt = insert(SlackUser).values(data)
        update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[
                SlackUser.__table__.c.slack_id,
            ],
            set_={
                "current_username": insert_stmt.excluded.current_username,
                "email": insert_stmt.excluded.email,
            },
        )
        db.execute(update_stmt)
        db.commit()


def get_users_to_invite(
    *,
    number_of_users_to_invite: int,
    event_id: UUID,
    total_number_of_employees: int,
    employees_per_event: int,
) -> list[SlackUser]:
    number_of_events_regarded = math.ceil(
        total_number_of_employees / employees_per_event
    )
    with session() as db:
        return (
            db.query(SlackUser)
            .join(
                Invitation,
                sa.and_(
                    Invitation.slack_user_id == SlackUser.slack_id,
                    Invitation.rsvp == RSVP.attending,
                    Invitation.event_id.in_(
                        db.query(Event.id)
                        .filter(Event.finalized == True)  # noqa
                        .order_by(Event.time.desc())
                        .limit(number_of_events_regarded)
                    ),
                ),
                isouter=True,
            )
            .filter(
                SlackUser.is_active == True,  # noqa
                SlackUser.is_opted_out == False,  # noqa
                SlackUser.slack_id.notin_(
                    db.query(Invitation.slack_user_id).filter(
                        Invitation.event_id == event_id,
                    )
                ),
            )
            .group_by(SlackUser.slack_id)
            .order_by(sa.func.count(Invitation.event_id).asc(), sa.func.random())
            .limit(number_of_users_to_invite)
            .all()
        )


def save_invitations(*, slack_users: list[SlackUser], event_id: UUID):
    with session() as db:
        for slack_user in slack_users:
            db.add(
                Invitation(
                    event_id=event_id,
                    slack_user_id=slack_user.slack_id,
                    rsvp=RSVP.unanswered,
                )
            )
        db.commit()


def get_event_in_need_of_invitations(
    *, days_in_advance_to_invite: int, people_per_event: int
) -> Optional[Event]:
    with session() as db:
        return (
            db.query(Event)
            .join(
                Invitation,
                sa.and_(
                    Invitation.event_id == Event.id,
                    Invitation.rsvp.in_((RSVP.unanswered, RSVP.attending)),  # type: ignore
                ),
                isouter=True,
            )
            .filter(
                Event.time > tz_aware_now(),
                Event.time < tz_aware_now() + timedelta(days=days_in_advance_to_invite),
            )
            .group_by(Event.id)
            .having(sa.func.count(Invitation.event_id) < people_per_event)
            .one_or_none()
        )


def get_number_of_invited_users(*, event_id: UUID) -> int:
    with session() as db:
        return (
            db.query(sa.func.count(Invitation.event_id))
            .filter(
                Invitation.event_id == event_id,
                Invitation.rsvp.in_([RSVP.unanswered, RSVP.attending]),  # type: ignore
            )
            .scalar()
        )


def get_invited_users() -> list[str]:
    with session() as db:
        return [
            row[0]
            for row in db.query(Invitation.slack_user_id)
            .filter(Invitation.rsvp == RSVP.unanswered)
            .all()
        ]


def rsvp(*, slack_id: str, answer: RSVP) -> None:
    with session() as db:
        invitation = (
            db.query(Invitation)
            .filter(
                Invitation.rsvp == RSVP.unanswered, Invitation.slack_user_id == slack_id
            )
            .first()
        )
        if not invitation:
            raise Exception("No invitation found for user ID, could not RSVP")

        invitation.rsvp = answer
        db.commit()


def mark_event_as_finalized(*, event_id: UUID):
    with session() as db:
        event = db.query(Event).filter(Event.id == event_id).one_or_none()
        if not event:
            raise Exception("No event found matching provided ID")

        event.finalized = True
        db.commit()


def get_event_ready_to_finalize(*, people_per_event) -> Optional[Event]:
    with session() as db:
        return (
            db.query(Event)
            .join(Invitation, Invitation.event_id == Event.id)
            .filter(Invitation.rsvp == RSVP.attending, Event.finalized == False)  # noqa
            .group_by(Event.id)
            .having(sa.func.count(Invitation.event_id) == people_per_event)
            .first()
        )


def get_unanswered_invitations() -> list[Invitation]:
    with session() as db:
        return db.query(Invitation).filter(Invitation.rsvp == RSVP.unanswered).all()


def get_attending_users(*, event_id: UUID) -> list[SlackUser]:
    with session() as db:
        return (
            db.query(SlackUser)
            .join(Invitation, Invitation.slack_user_id == SlackUser.slack_id)
            .filter(Invitation.rsvp == RSVP.attending, Invitation.event_id == event_id)
            .order_by(sa.func.random())
            .all()
        )


def get_slack_ids_from_emails(*, emails: list[str]) -> list[SlackUser]:
    with session() as db:
        return db.query(SlackUser).filter(SlackUser.email.in_(emails)).all()


def update_reminded_at(*, slack_id):
    with session() as db:
        invitation = (
            db.query(Invitation)
            .filter(
                Invitation.slack_user_id == slack_id, Invitation.rsvp == RSVP.unanswered
            )
            .one_or_none()
        )
        if not invitation:
            raise Exception("No unanswered invitation found for slack user")

        invitation.reminded_at = tz_aware_now()
        db.commit()


def auto_reply_after_deadline(*, deadline_hours: int) -> list[str]:
    with session() as db:
        invitations = (
            db.query(Invitation)
            .filter(
                (
                    Invitation.invited_at
                    < tz_aware_now() - timedelta(hours=deadline_hours)
                ),
                Invitation.rsvp == RSVP.unanswered,
            )
            .all()
        )
        for invitation in invitations:
            invitation.rsvp = RSVP.not_attending
        db.commit()
        return [invitation.slack_user_id for inviations in invitations]


def get_number_of_slack_users() -> int:
    with session() as db:
        return (
            db.query(sa.func.count(SlackUser.slack_id))
            .filter(
                SlackUser.is_active == True,  # noqa
            )
            .scalar()
        )
