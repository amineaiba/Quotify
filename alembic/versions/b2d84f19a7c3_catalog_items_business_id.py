"""catalog_items business_id

Revision ID: b2d84f19a7c3
Revises: a1c9f47e2b6d
Create Date: 2026-09-01 00:00:00.000000

Existing catalog rows are fake seed data (see CLAUDE.md) with no business
to attach to — truncated rather than backfilled.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2d84f19a7c3"
down_revision: str | Sequence[str] | None = "a1c9f47e2b6d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("TRUNCATE TABLE catalog_item_tiers, catalog_items RESTART IDENTITY CASCADE")
    op.add_column(
        "catalog_items",
        sa.Column("business_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_foreign_key(
        "catalog_items_business_id_fkey",
        "catalog_items",
        "businesses",
        ["business_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("catalog_items_business_id_fkey", "catalog_items", type_="foreignkey")
    op.drop_column("catalog_items", "business_id")
