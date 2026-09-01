import random
import uuid

import pytest

from app.core.exceptions import BelowMinimumQuantity, ItemNotFound
from app.llm.embeddings import EMBED_DIM
from app.models.catalog import CatalogItem, CatalogItemTier
from app.services.pricing import calc_price, pick_tier
from tests.conftest import make_business

# Flyer A5 quadri recto-verso
FLYER_TIERS = [
    CatalogItemTier(min_qty=100, unit_price=30),
    CatalogItemTier(min_qty=500, unit_price=19),
    CatalogItemTier(min_qty=1000, unit_price=14),
    CatalogItemTier(min_qty=5000, unit_price=10),
]


@pytest.mark.parametrize(
    ("quantity", "expected_unit_price", "expected_min_qty"),
    [
        (500, 19, 500),
        (100, 30, 100),
        (999, 19, 500),
        (9000, 10, 5000),
    ],
)
def test_pick_tier(quantity, expected_unit_price, expected_min_qty):
    tier = pick_tier(FLYER_TIERS, quantity)

    assert tier.unit_price == expected_unit_price
    assert tier.min_qty == expected_min_qty


def test_pick_tier_ignores_row_order():
    shuffled = list(FLYER_TIERS)
    random.shuffle(shuffled)

    tier = pick_tier(shuffled, 999)

    assert tier.min_qty == 500
    assert tier.unit_price == 19


def test_pick_tier_below_minimum_raises():
    with pytest.raises(BelowMinimumQuantity) as exc_info:
        pick_tier(FLYER_TIERS, 50)

    assert exc_info.value.min_qty == 100


async def test_calc_price_happy_path(session):
    business = await make_business(session)
    item = CatalogItem(
        business_id=business.id,
        name="Flyer A5 quadri recto-verso",
        unit="flyer",
        tiers=[CatalogItemTier(min_qty=t.min_qty, unit_price=t.unit_price) for t in FLYER_TIERS],
        embedding=[0.0] * EMBED_DIM,
    )
    session.add(item)
    await session.commit()

    breakdown = await calc_price(session, item_id=item.id, quantity=500)

    assert breakdown.name == "Flyer A5 quadri recto-verso"
    assert breakdown.unit == "flyer"
    assert breakdown.quantity == 500
    assert breakdown.unit_price == 19
    assert breakdown.applied_min_qty == 500
    assert breakdown.total == 9500


async def test_calc_price_unknown_item_raises(session):
    unknown_id = uuid.uuid4()

    with pytest.raises(ItemNotFound) as exc_info:
        await calc_price(session, item_id=unknown_id, quantity=500)

    assert exc_info.value.item_id == unknown_id
