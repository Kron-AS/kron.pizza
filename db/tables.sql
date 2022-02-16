CREATE EXTENSION "uuid-ossp";
SET TIMEZONE TO 'Europe/Oslo';

CREATE TABLE slack_users (
  slack_id TEXT NOT NULL PRIMARY KEY,
  current_username TEXT NOT NULL,
  email TEXT NOT NULL,
  first_seen DATE NOT NULL DEFAULT NOW(),
  active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE events (
  id TEXT PRIMARY KEY DEFAULT uuid_generate_v4(),
  time TIMESTAMPTZ NOT NULL,
  place TEXT NOT NULL,
  finalized BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TYPE RSVP AS ENUM ('attending', 'not attending', 'unanswered');

CREATE TABLE invitations (
  event_id TEXT REFERENCES events (id),
  slack_id TEXT REFERENCES slack_users (slack_id),
  invited_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reminded_at TIMESTAMPTZ,
  rsvp RSVP NOT NULL DEFAULT 'unanswered',
  PRIMARY KEY (event_id, slack_id)
);

CREATE TABLE images (
  cloudinary_id TEXT PRIMARY KEY,
  uploaded_by TEXT REFERENCES slack_users (slack_id),
  uploaded_at TIMESTAMPTZ DEFAULT NOW(),
  title TEXT
);
