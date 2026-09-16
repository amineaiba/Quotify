import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_business
from app.core.exceptions import QuoteNotPending
from app.db.session import get_session
from app.models.business import Business
from app.models.conversation import Sender
from app.models.quote import Quote, QuoteStatus
from app.schemas.pricing import PriceBreakdown
from app.schemas.quote import QuoteActionResponse, QuoteApproveRequest, QuoteListItem
from app.services.conversation import save_message
from app.services.quotes import (
    QuoteRow,
    approve_quote,
    get_quote_for_business,
    list_quotes,
    reject_quote,
)
from app.whatsapp.client import send_message

router = APIRouter()


def _quote_total(lines: list[dict] | None) -> int | None:
    if not lines:
        return None
    return sum(line["total"] for line in lines)


def _to_list_item(row: QuoteRow) -> QuoteListItem:
    return QuoteListItem(
        id=row.quote.id,
        conversation_id=row.conversation.id,
        client=row.client,
        draft_message=row.quote.draft_message,
        confidence=row.quote.confidence,
        status=row.quote.status,
        hold_reason=row.quote.hold_reason,
        lines=[PriceBreakdown.model_validate(line) for line in (row.quote.lines or [])],
        subtotal=_quote_total(row.quote.lines),
        created_at=row.quote.created_at,
    )


def _to_action_response(quote: Quote) -> QuoteActionResponse:
    return QuoteActionResponse(
        id=quote.id,
        status=quote.status,
        final_message=quote.final_message,
        reviewed_at=quote.reviewed_at,
    )


@router.get("", response_model=list[QuoteListItem])
async def list_quotes_endpoint(
    status_filter: QuoteStatus | None = Query(default=None, alias="status"),
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> list[QuoteListItem]:
    rows = await list_quotes(session, business.id, status=status_filter)
    return [_to_list_item(row) for row in rows]


@router.post("/{quote_id}/approve", response_model=QuoteActionResponse)
async def approve_quote_endpoint(
    quote_id: uuid.UUID,
    body: QuoteApproveRequest,
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> QuoteActionResponse:
    row = await get_quote_for_business(session, business.id, quote_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        quote = await approve_quote(session, row.quote, body.message)
    except QuoteNotPending as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="quote is not pending"
        ) from exc

    await save_message(session, row.conversation.id, Sender.agent, body.message)
    await send_message(business.whatsapp_phone_number_id, row.client.phone_number, body.message)

    return _to_action_response(quote)


@router.post("/{quote_id}/reject", response_model=QuoteActionResponse)
async def reject_quote_endpoint(
    quote_id: uuid.UUID,
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> QuoteActionResponse:
    row = await get_quote_for_business(session, business.id, quote_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    try:
        quote = await reject_quote(session, row.quote)
    except QuoteNotPending as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="quote is not pending"
        ) from exc

    return _to_action_response(quote)
