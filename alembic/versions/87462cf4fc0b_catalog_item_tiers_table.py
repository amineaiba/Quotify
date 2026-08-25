"""catalog_item_tiers table

Revision ID: 87462cf4fc0b
Revises: 330beb92ddbe
Create Date: 2026-08-24 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '87462cf4fc0b'
down_revision: str | Sequence[str] | None = '330beb92ddbe'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "catalog_item_tiers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("catalog_item_id", sa.Integer(), nullable=False),
        sa.Column("min_qty", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["catalog_item_id"], ["catalog_items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalog_item_id", "min_qty"),
    )

    # Backfill from the JSON column before dropping it.
    op.execute(
        """
        INSERT INTO catalog_item_tiers (catalog_item_id, min_qty, unit_price)
        SELECT id, (t->>'min_qty')::int, (t->>'unit_price')::int
        FROM catalog_items, json_array_elements(tiers) AS t
        """
    )

    op.drop_column("catalog_items", "tiers")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("catalog_items", sa.Column("tiers", sa.JSON(), nullable=True))

    op.execute(
        """
        UPDATE catalog_items
        SET tiers = sub.tiers
        FROM (
            SELECT catalog_item_id,
                   json_agg(
                       json_build_object('min_qty', min_qty, 'unit_price', unit_price)
                       ORDER BY min_qty
                   ) AS tiers
            FROM catalog_item_tiers
            GROUP BY catalog_item_id
        ) AS sub
        WHERE catalog_items.id = sub.catalog_item_id
        """
    )

    op.alter_column("catalog_items", "tiers", nullable=False)
    op.drop_table("catalog_item_tiers")
