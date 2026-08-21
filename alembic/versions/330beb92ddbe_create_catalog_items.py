"""create catalog_items

Revision ID: 330beb92ddbe
Revises: 
Create Date: 2026-08-20 16:33:34.272336

"""
from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '330beb92ddbe'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Must run before the table below — the vector column type doesn't
    # exist until the extension is turned on. Alembic never adds this on
    # its own, autogenerate included.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "catalog_items",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("tiers", sa.JSON(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(3072), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    # No index: HNSW/IVFFlat cap at 2,000 dims, this column is 3072.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("catalog_items")
    op.execute("DROP EXTENSION IF EXISTS vector")
