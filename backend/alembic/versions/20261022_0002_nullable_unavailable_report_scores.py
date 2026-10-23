"""Represent unavailable report scores as NULL instead of a zero sentinel.

Revision ID: 20261022_0002
Revises: 20260716_0001
"""

from alembic import op
import sqlalchemy as sa


revision = "20261022_0002"
down_revision = "20260716_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Previous code explicitly stored 0 only alongside this status when
    # evidence was incomplete. Preserve genuine measured zero scores.
    op.execute(
        "UPDATE interviews SET integrity_score = NULL "
        "WHERE risk_level = 'review_required' AND integrity_score = 0"
    )
    with op.batch_alter_table("reports") as batch_op:
        batch_op.alter_column(
            "integrity_score",
            existing_type=sa.Float(),
            nullable=True,
        )
    op.execute(
        "UPDATE reports SET integrity_score = NULL "
        "WHERE risk_level = 'review_required' AND integrity_score = 0"
    )


def downgrade() -> None:
    # Lossy downgrade: unavailable NULL scores become indistinguishable from
    # genuine measured zeroes when restored to the previous NOT NULL schema.
    op.execute("UPDATE reports SET integrity_score = 0 WHERE integrity_score IS NULL")
    with op.batch_alter_table("reports") as batch_op:
        batch_op.alter_column(
            "integrity_score",
            existing_type=sa.Float(),
            nullable=False,
        )
