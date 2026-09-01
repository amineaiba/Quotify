"""switch all ids to uuid

Revision ID: a1c9f47e2b6d
Revises: d81f4b6a2c53
Create Date: 2026-08-31 00:00:00.000000

All existing data is fake (portfolio project, see CLAUDE.md) — this
truncates every app table instead of converting int ids to uuid in place.
gen_random_uuid() is built into Postgres 13+, no extension needed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1c9f47e2b6d"
down_revision: str | Sequence[str] | None = "d81f4b6a2c53"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)

# (table, column) pairs that carry a PK sequence today — catalog_items.id
# is the one PK with no sequence (created autoincrement=False).
_SEQUENCE_COLUMNS = [
    ("businesses", "id"),
    ("clients", "id"),
    ("catalog_item_tiers", "id"),
    ("conversations", "id"),
    ("messages", "id"),
    ("refresh_tokens", "id"),
]

_ALL_ID_COLUMNS = [
    ("businesses", "id"),
    ("clients", "id"),
    ("clients", "business_id"),
    ("catalog_items", "id"),
    ("catalog_item_tiers", "id"),
    ("catalog_item_tiers", "catalog_item_id"),
    ("conversations", "id"),
    ("conversations", "business_id"),
    ("conversations", "client_id"),
    ("messages", "id"),
    ("messages", "conversation_id"),
    ("refresh_tokens", "id"),
    ("refresh_tokens", "business_id"),
]

_FOREIGN_KEYS = [
    # (constraint name, table, column, referenced table)
    (
        "catalog_item_tiers_catalog_item_id_fkey",
        "catalog_item_tiers",
        "catalog_item_id",
        "catalog_items",
    ),
    ("clients_business_id_fkey", "clients", "business_id", "businesses"),
    ("conversations_business_id_fkey", "conversations", "business_id", "businesses"),
    ("conversations_client_id_fkey", "conversations", "client_id", "clients"),
    ("messages_conversation_id_fkey", "messages", "conversation_id", "conversations"),
    ("refresh_tokens_business_id_fkey", "refresh_tokens", "business_id", "businesses"),
]


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "TRUNCATE TABLE refresh_tokens, messages, conversations, "
        "catalog_item_tiers, catalog_items, clients, businesses "
        "RESTART IDENTITY CASCADE"
    )

    for name, table, _column, _referenced in _FOREIGN_KEYS:
        op.drop_constraint(name, table, type_="foreignkey")

    for table, column in _SEQUENCE_COLUMNS:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} DROP DEFAULT")

    for table, column in _ALL_ID_COLUMNS:
        # Tables are empty (just truncated) — nothing to preserve, USING
        # NULL just satisfies Postgres's "give me a cast" requirement.
        op.alter_column(
            table,
            column,
            existing_type=sa.Integer(),
            type_=UUID,
            postgresql_using="NULL",
        )

    for table, _column in _SEQUENCE_COLUMNS:
        op.execute(f'DROP SEQUENCE IF EXISTS "{table}_id_seq"')

    for name, table, column, referenced in _FOREIGN_KEYS:
        op.create_foreign_key(name, table, referenced, [column], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "TRUNCATE TABLE refresh_tokens, messages, conversations, "
        "catalog_item_tiers, catalog_items, clients, businesses "
        "RESTART IDENTITY CASCADE"
    )

    for name, table, _column, _referenced in _FOREIGN_KEYS:
        op.drop_constraint(name, table, type_="foreignkey")

    for table, column in _ALL_ID_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=UUID,
            type_=sa.Integer(),
            postgresql_using="NULL",
        )

    for table, column in _SEQUENCE_COLUMNS:
        op.execute(f'CREATE SEQUENCE "{table}_id_seq" OWNED BY {table}.{column}')
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT nextval('\"{table}_id_seq\"')"
        )
    # catalog_items.id is left with no default — matches the original
    # migration, which created it autoincrement=False.

    for name, table, column, referenced in _FOREIGN_KEYS:
        op.create_foreign_key(name, table, referenced, [column], ["id"], ondelete="CASCADE")
