"""practice question source

Revision ID: 0002_question_source
Revises: 0001_initial
Create Date: 2026-10-19 08:00:00

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_question_source"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("practice_sessions") as batch_op:
        batch_op.add_column(
            sa.Column("question_source", sa.String(length=30), nullable=False, server_default="question_bank")
        )


def downgrade() -> None:
    with op.batch_alter_table("practice_sessions") as batch_op:
        batch_op.drop_column("question_source")
