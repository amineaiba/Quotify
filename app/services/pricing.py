from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BelowMinimumQuantity, ItemNotFound
from app.models.catalog import CatalogItem, CatalogItemTier
from app.schemas.pricing import PriceBreakdown


def pick_tier(tiers: list[CatalogItemTier], quantity: int) -> CatalogItemTier:
    """Highest tier whose min_qty <= quantity — bigger order, cheaper unit."""
    eligible = [tier for tier in tiers if tier.min_qty <= quantity]
    if not eligible:
        raise BelowMinimumQuantity(min_qty=min(t.min_qty for t in tiers))
    return max(eligible, key=lambda t: t.min_qty)


async def calc_price(session: AsyncSession, item_id: int, quantity: int) -> PriceBreakdown:
    """Look up item_id, pick the tier for quantity, compose the breakdown."""
    item = await session.get(
        CatalogItem, item_id, options=[selectinload(CatalogItem.tiers)]
    )
    if item is None:
        raise ItemNotFound(item_id=item_id)

    tier = pick_tier(item.tiers, quantity)

    return PriceBreakdown(
        item_id=item.id,
        name=item.name,
        unit=item.unit,
        quantity=quantity,
        unit_price=tier.unit_price,
        applied_min_qty=tier.min_qty,
        total=quantity * tier.unit_price,
    )
