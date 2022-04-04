"""add is opted out

Revision ID: e55ad77eccdd
Revises: 2ff39dd5a9cc
Create Date: 2022-04-04 21:25:52.964891

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e55ad77eccdd"
down_revision = "2ff39dd5a9cc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("slack_users", sa.Column("is_opted_out", sa.Boolean(), nullable=True))
    op.execute("UPDATE slack_users SET is_opted_out = false")
    op.execute("ALTER TABLE slack_users ALTER COLUMN is_opted_out NOT NULL")


def downgrade():
    op.drop_column("slack_users", "is_opted_out")
