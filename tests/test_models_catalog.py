import pytest
from sqlalchemy.exc import IntegrityError

from app.llm.embeddings import EMBED_DIM
from app.models.business import Business
from app.models.catalog import CatalogItem, CatalogItemTier


async def _make_business(session) -> Business:
    business = Business(
        name="Atelier Print",
        email="owner@atelier.dz",
        hashed_password="hashed",
        api_key="key-1",
    )
    session.add(business)
    await session.flush()
    return business


async def test_catalog_item_requires_business_id(session):
    session.add(CatalogItem(name="Flyer", unit="flyer", embedding=[0.0] * EMBED_DIM))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_catalog_item_belongs_to_business(session):
    business = await _make_business(session)
    item = CatalogItem(
        business_id=business.id, name="Flyer", unit="flyer", embedding=[0.0] * EMBED_DIM
    )
    session.add(item)
    await session.commit()

    assert item.business_id == business.id


async def test_deleting_business_cascades_to_catalog_items(session):
    business = await _make_business(session)
    item = CatalogItem(
        business_id=business.id, name="Flyer", unit="flyer", embedding=[0.0] * EMBED_DIM
    )
    item.tiers = [CatalogItemTier(min_qty=1, unit_price=10)]
    session.add(item)
    await session.commit()
    item_id = item.id

    await session.delete(business)
    await session.commit()
    session.expire_all()  # DB-level ON DELETE CASCADE — session doesn't know on its own

    assert await session.get(CatalogItem, item_id) is None
