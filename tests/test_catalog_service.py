import uuid

import pytest

from app.llm.embeddings import EMBED_DIM
from app.schemas.catalog import CatalogItemWrite
from app.services.catalog import create_item, delete_item, get_item, list_items, update_item
from tests.conftest import make_business

FAKE_VECTOR = [0.1] * EMBED_DIM


def fake_embed(texts: list[str], task_type: str) -> list[list[float]]:
    return [FAKE_VECTOR for _ in texts]


@pytest.fixture(autouse=True)
def _fake_embed(monkeypatch):
    monkeypatch.setattr("app.services.catalog.embed", fake_embed)


async def test_create_item_embeds_name_and_saves_tiers(session):
    business = await make_business(session)
    data = CatalogItemWrite(
        name="Flyer A5",
        unit="flyer",
        tiers=[{"min_qty": 100, "unit_price": 10}, {"min_qty": 500, "unit_price": 8}],
    )

    item = await create_item(session, business.id, data)

    assert item.business_id == business.id
    assert item.embedding == FAKE_VECTOR
    assert [t.min_qty for t in item.tiers] == [100, 500]


async def test_list_items_scoped_to_business(session):
    business_a = await make_business(session, email="a@x.com", api_key="ka")
    business_b = await make_business(session, email="b@x.com", api_key="kb")
    await create_item(
        session,
        business_a.id,
        CatalogItemWrite(name="A", unit="u", tiers=[{"min_qty": 1, "unit_price": 1}]),
    )
    await create_item(
        session,
        business_b.id,
        CatalogItemWrite(name="B", unit="u", tiers=[{"min_qty": 1, "unit_price": 1}]),
    )

    items = await list_items(session, business_a.id)

    assert [i.name for i in items] == ["A"]


async def test_get_item_returns_none_for_other_business(session):
    business_a = await make_business(session, email="a2@x.com", api_key="ka2")
    business_b = await make_business(session, email="b2@x.com", api_key="kb2")
    item = await create_item(
        session,
        business_a.id,
        CatalogItemWrite(name="A", unit="u", tiers=[{"min_qty": 1, "unit_price": 1}]),
    )

    assert await get_item(session, business_b.id, item.id) is None
    assert (await get_item(session, business_a.id, item.id)).id == item.id


async def test_update_item_reembeds_only_on_name_change(session, monkeypatch):
    business = await make_business(session)
    item = await create_item(
        session,
        business.id,
        CatalogItemWrite(name="A", unit="u", tiers=[{"min_qty": 1, "unit_price": 1}]),
    )
    calls = []
    monkeypatch.setattr(
        "app.services.catalog.embed",
        lambda texts, task_type: calls.append(texts) or [FAKE_VECTOR for _ in texts],
    )

    # same name, different price — no re-embed
    await update_item(
        session,
        business.id,
        item.id,
        CatalogItemWrite(name="A", unit="u", tiers=[{"min_qty": 1, "unit_price": 2}]),
    )
    assert calls == []

    # name changes — re-embed
    await update_item(
        session,
        business.id,
        item.id,
        CatalogItemWrite(name="B", unit="u", tiers=[{"min_qty": 1, "unit_price": 2}]),
    )
    assert calls == [["B"]]


async def test_update_item_returns_none_for_unknown_item(session):
    business = await make_business(session)
    result = await update_item(
        session,
        business.id,
        uuid.uuid4(),
        CatalogItemWrite(name="A", unit="u", tiers=[{"min_qty": 1, "unit_price": 1}]),
    )
    assert result is None


async def test_delete_item_removes_row_and_returns_true(session):
    business = await make_business(session)
    item = await create_item(
        session,
        business.id,
        CatalogItemWrite(name="A", unit="u", tiers=[{"min_qty": 1, "unit_price": 1}]),
    )

    deleted = await delete_item(session, business.id, item.id)

    assert deleted is True
    assert await get_item(session, business.id, item.id) is None


async def test_delete_item_returns_false_for_unknown_item(session):
    business = await make_business(session)
    assert await delete_item(session, business.id, uuid.uuid4()) is False
