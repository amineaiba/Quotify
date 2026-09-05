"""whatsapp columns

Revision ID: 66fd9894963c
Revises: b2d84f19a7c3
Create Date: 2026-09-05 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "66fd9894963c"
down_revision: str | Sequence[str] | None = "b2d84f19a7c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("businesses", sa.Column("whatsapp_phone_number_id", sa.String(), nullable=True))
    op.create_unique_constraint(
        "businesses_whatsapp_phone_number_id_key", "businesses", ["whatsapp_phone_number_id"]
    )
    op.create_unique_constraint(
        "conversations_business_id_client_id_channel_key",
        "conversations",
        ["business_id", "client_id", "channel"],
    )
    op.add_column("messages", sa.Column("whatsapp_message_id", sa.String(), nullable=True))
    op.create_unique_constraint(
        "messages_whatsapp_message_id_key", "messages", ["whatsapp_message_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("messages_whatsapp_message_id_key", "messages", type_="unique")
    op.drop_column("messages", "whatsapp_message_id")
    op.drop_constraint(
        "conversations_business_id_client_id_channel_key", "conversations", type_="unique"
    )
    op.drop_constraint("businesses_whatsapp_phone_number_id_key", "businesses", type_="unique")
    op.drop_column("businesses", "whatsapp_phone_number_id")
