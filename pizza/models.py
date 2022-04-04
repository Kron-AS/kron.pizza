from enum import Enum

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg
import sqlalchemy.engine
from sqlalchemy import Column
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RSVP(Enum):
    attending = "attending"
    not_attending = "not attending"
    unanswered = "unanswered"


class SlackUser(Base):
    __tablename__ = "slack_users"
    slack_id = Column(sa.Text, primary_key=True)
    current_username = Column(sa.Text, nullable=False)
    email = Column(sa.Text, nullable=False)
    first_seen_at = Column(sa.Date, nullable=False, server_default=sa.func.now())
    is_active = Column(sa.Boolean, nullable=False, default=True)
    is_opted_out = Column(sa.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"SlackUser(id={self.slack_id!r}, current_username={self.current_username!r}, email={self.email!r})"


class Event(Base):
    __tablename__ = "events"
    id = Column(
        pg.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )
    time = Column(sa.DateTime(timezone=True), nullable=False)
    location = Column(sa.Text, nullable=False)
    finalized = Column(sa.Boolean, nullable=False, default=False, server_default="f")


class Invitation(Base):
    __tablename__ = "invitations"
    event_id = Column(
        pg.UUID(as_uuid=True), sa.ForeignKey(Event.id), nullable=False, primary_key=True
    )
    slack_user_id = Column(
        sa.Text,
        sa.ForeignKey(SlackUser.slack_id),
        nullable=False,
        primary_key=True,
    )
    invited_at = Column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    reminded_at = Column(sa.DateTime(timezone=True), nullable=True)
    rsvp: RSVP = Column(sa.Enum(RSVP, native_enum=False), default=RSVP.unanswered)  # type: ignore

    __table_args__ = (sa.UniqueConstraint(event_id, slack_user_id),)
