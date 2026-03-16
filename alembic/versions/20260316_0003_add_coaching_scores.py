"""add coaching scores

Revision ID: 20260316_0003
Revises: 20260310_0002
Create Date: 2026-03-16 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_0003"
down_revision = "20260310_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coaching_scores",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("workout_id", sa.String(length=36), sa.ForeignKey("workout_history.id"), nullable=False, unique=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("hr_score", sa.Integer(), nullable=True),
        sa.Column("breath_score", sa.Integer(), nullable=True),
        sa.Column("duration_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_coaching_scores_user_id", "coaching_scores", ["user_id"])
    op.create_index("ix_coaching_scores_created_at", "coaching_scores", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_coaching_scores_created_at", table_name="coaching_scores")
    op.drop_index("ix_coaching_scores_user_id", table_name="coaching_scores")
    op.drop_table("coaching_scores")
