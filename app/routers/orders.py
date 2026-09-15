import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_business
from app.db.session import get_session
from app.models.business import Business
from app.schemas.conversation import QuoteSummary
from app.schemas.order import OrderDetail, OrderSummary
from app.schemas.pricing import PriceBreakdown
from app.services.orders import OrderRow, get_order_for_business, list_orders

router = APIRouter()


def _quote_total(lines: list[dict]) -> int:
    return sum(line["total"] for line in lines)


def _to_summary(row: OrderRow) -> OrderSummary:
    return OrderSummary(
        id=row.order.id,
        created_at=row.order.created_at,
        status=row.order.status,
        client=row.client,
        channel=row.conversation.channel,
        quote=QuoteSummary(
            status=row.quote.status,
            lines=[PriceBreakdown.model_validate(line) for line in row.quote.lines],
            subtotal=_quote_total(row.quote.lines),
        ),
    )


@router.get("", response_model=list[OrderSummary])
async def list_orders_endpoint(
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> list[OrderSummary]:
    rows = await list_orders(session, business.id)
    return [_to_summary(row) for row in rows]


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order_endpoint(
    order_id: uuid.UUID,
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> OrderDetail:
    row = await get_order_for_business(session, business.id, order_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    summary = _to_summary(row)
    return OrderDetail(**summary.model_dump(), conversation_id=row.conversation.id)
