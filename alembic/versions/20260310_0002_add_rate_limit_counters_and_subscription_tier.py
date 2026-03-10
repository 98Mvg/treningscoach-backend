"""add rate limit counters and user subscriptions

Revision ID: 20260310_0002
Revises: 20260304_0001
Create Date: 2026-03-10 12:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260310_0002"
down_revision = "20260304_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_subscriptions",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("tier", sa.String(length=20), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "rate_limit_counters",
        sa.Column("subject_key", sa.String(length=255), nullable=False),
        sa.Column("rule_name", sa.String(length=120), nullable=False),
        sa.Column("window_start", sa.Integer(), nullable=False),
        sa.Column("window_seconds", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("subject_key", "rule_name", "window_start"),
    )
    op.create_index("ix_rate_limit_counters_updated_at", "rate_limit_counters", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_rate_limit_counters_updated_at", table_name="rate_limit_counters")
    op.drop_table("rate_limit_counters")
    op.drop_table("user_subscriptions")
