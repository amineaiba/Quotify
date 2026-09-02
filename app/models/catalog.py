import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.llm.embeddings import EMBED_DIM


class CatalogItem(Base):
    __tablename__ = "catalog_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    unit: Mapped[str] = mapped_column(nullable=False)

    tiers: Mapped[list["CatalogItemTier"]] = relationship(
        order_by="CatalogItemTier.min_qty",
        cascade="all, delete-orphan",
    )

    embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIM), nullable=False)


class CatalogItemTier(Base):
    __tablename__ = "catalog_item_tiers"
    __table_args__ = (UniqueConstraint("catalog_item_id", "min_qty"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    catalog_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog_items.id", ondelete="CASCADE"), nullable=False
    )
    min_qty: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[int] = mapped_column(nullable=False)
