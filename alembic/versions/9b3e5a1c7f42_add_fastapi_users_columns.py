"""add fastapi-users columns to businesses

Revision ID: 9b3e5a1c7f42
Revises: 5f0a1c8e93d4
Create Date: 2026-08-28 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9b3e5a1c7f42'
down_revision: str | Sequence[str] | None = '5f0a1c8e93d4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "businesses",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "businesses",
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "businesses",
        sa.Column("is_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("businesses", "is_verified")
    op.drop_column("businesses", "is_superuser")
    op.drop_column("businesses", "is_active")
