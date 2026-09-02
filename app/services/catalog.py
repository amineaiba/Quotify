import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.embeddings import embed
from app.models.catalog import CatalogItem, CatalogItemTier
from app.schemas.catalog import CatalogItemWrite


async def search_catalog(session: AsyncSession, message: str, k: int = 3) -> list[CatalogItem]:
    """Top k catalog items closest in meaning to `message`, best match first."""
    [query_vector] = embed([message], "RETRIEVAL_QUERY")

    # cosine_distance: smaller = closer. DESC here would return the worst matches.
    stmt = (
        select(CatalogItem)
        .order_by(CatalogItem.embedding.cosine_distance(query_vector))
        .limit(k)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_items(session: AsyncSession, business_id: uuid.UUID) -> list[CatalogItem]:
    stmt = (
        select(CatalogItem)
        .where(CatalogItem.business_id == business_id)
        .options(selectinload(CatalogItem.tiers))
        .order_by(CatalogItem.name)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_item(
    session: AsyncSession, business_id: uuid.UUID, item_id: uuid.UUID
) -> CatalogItem | None:
    stmt = (
        select(CatalogItem)
        .where(CatalogItem.business_id == business_id, CatalogItem.id == item_id)
        .options(selectinload(CatalogItem.tiers))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_item(
    session: AsyncSession, business_id: uuid.UUID, data: CatalogItemWrite
) -> CatalogItem:
    [vector] = embed([data.name], "RETRIEVAL_DOCUMENT")
    item = CatalogItem(
        business_id=business_id,
        name=data.name,
        unit=data.unit,
        embedding=vector,
        tiers=[CatalogItemTier(min_qty=t.min_qty, unit_price=t.unit_price) for t in data.tiers],
    )
    session.add(item)
    await session.commit()
    await session.refresh(item, attribute_names=["tiers"])
    return item


async def update_item(
    session: AsyncSession, business_id: uuid.UUID, item_id: uuid.UUID, data: CatalogItemWrite
) -> CatalogItem | None:
    item = await get_item(session, business_id, item_id)
    if item is None:
        return None

    if item.name != data.name:
        [vector] = embed([data.name], "RETRIEVAL_DOCUMENT")
        item.embedding = vector

    item.name = data.name
    item.unit = data.unit

    # Old tiers must be gone before the new ones are inserted, or a
    # min_qty shared between an old and new tier trips the unique
    # constraint mid-flush (delete-orphan alone doesn't order this).
    for tier in list(item.tiers):
        await session.delete(tier)
    await session.flush()
    item.tiers = [CatalogItemTier(min_qty=t.min_qty, unit_price=t.unit_price) for t in data.tiers]

    await session.commit()
    await session.refresh(item, attribute_names=["tiers"])
    return item


async def delete_item(session: AsyncSession, business_id: uuid.UUID, item_id: uuid.UUID) -> bool:
    item = await get_item(session, business_id, item_id)
    if item is None:
        return False
    await session.delete(item)
    await session.commit()
    return True
