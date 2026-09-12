"""conversations last_message_at

Revision ID: ac50b242b284
Revises: 8a11ef6ea665
Create Date: 2026-09-11 09:40:47.102644

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ac50b242b284'
down_revision: str | Sequence[str] | None = '8a11ef6ea665'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "conversations",
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        """
        UPDATE conversations c
        SET last_message_at = (
            SELECT MAX(m.created_at) FROM messages m WHERE m.conversation_id = c.id
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("conversations", "last_message_at")
