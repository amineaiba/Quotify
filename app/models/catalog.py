from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.llm.embeddings import EMBED_DIM


class CatalogItem(Base):
    __tablename__ = "catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(nullable=False)
    unit: Mapped[str] = mapped_column(nullable=False)

    # Ordered list of {"min_qty", "unit_price"} — not an int-keyed dict.
    # JSON has no integer keys, so a dict silently sorts wrong on lookup.
    tiers: Mapped[list] = mapped_column(JSON, nullable=False)

    embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIM), nullable=False)
