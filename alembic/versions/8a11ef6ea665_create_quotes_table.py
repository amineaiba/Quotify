"""create quotes table

Revision ID: 8a11ef6ea665
Revises: 66fd9894963c
Create Date: 2026-09-09 16:06:42.799842

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '8a11ef6ea665'
down_revision: str | Sequence[str] | None = '66fd9894963c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("draft_message", sa.String(), nullable=False),
        sa.Column("final_message", sa.String(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "approved", "rejected", "auto_sent",
                name="quote_status", native_enum=False, create_constraint=True, length=20,
            ),
            nullable=False,
        ),
        sa.Column(
            "hold_reason",
            sa.Enum(
                "low_confidence", "rate_limited",
                name="hold_reason", native_enum=False, create_constraint=True, length=20,
            ),
            nullable=True,
        ),
        sa.Column("lines", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("quotes")
