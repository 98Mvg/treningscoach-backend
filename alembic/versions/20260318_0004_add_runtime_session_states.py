"""add runtime session states

Revision ID: 20260318_0004
Revises: 20260316_0003
Create Date: 2026-03-18 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260318_0004"
down_revision = "20260316_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_session_states",
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index("ix_runtime_session_states_user_id", "runtime_session_states", ["user_id"], unique=False)
    op.create_index("ix_runtime_session_states_updated_at", "runtime_session_states", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_runtime_session_states_updated_at", table_name="runtime_session_states")
    op.drop_index("ix_runtime_session_states_user_id", table_name="runtime_session_states")
    op.drop_table("runtime_session_states")
