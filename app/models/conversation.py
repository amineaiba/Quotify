import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Channel(enum.StrEnum):
    whatsapp = "whatsapp"


class Sender(enum.StrEnum):
    client = "client"
    agent = "agent"
    staff = "staff"


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("business_id", "client_id", "channel"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[Channel] = mapped_column(
        Enum(Channel, name="channel", native_enum=False, create_constraint=True, length=20),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender: Mapped[Sender] = mapped_column(
        Enum(Sender, name="sender", native_enum=False, create_constraint=True, length=20),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(nullable=False)
    whatsapp_message_id: Mapped[str | None] = mapped_column(unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
