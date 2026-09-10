import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuoteStatus(enum.StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    auto_sent = "auto_sent"


class HoldReason(enum.StrEnum):
    low_confidence = "low_confidence"
    rate_limited = "rate_limited"


class Quote(Base):
    """One row per agent reply, whether it auto-sent or was held for review."""

    __tablename__ = "quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    draft_message: Mapped[str] = mapped_column(String, nullable=False)
    final_message: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[QuoteStatus] = mapped_column(
        Enum(
            QuoteStatus, name="quote_status", native_enum=False, create_constraint=True, length=20
        ),
        nullable=False,
    )
    hold_reason: Mapped[HoldReason | None] = mapped_column(
        Enum(HoldReason, name="hold_reason", native_enum=False, create_constraint=True, length=20),
        nullable=True,
    )
    lines: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
