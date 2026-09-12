import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_business
from app.db.session import get_session
from app.models.business import Business
from app.schemas.conversation import ConversationDetail, ConversationSummary, QuoteSummary
from app.schemas.pricing import PriceBreakdown
from app.services.conversation import (
    ConversationSummaryRow,
    derive_conversation_status,
    get_conversation_thread,
    list_conversations,
)

router = APIRouter()


def _quote_total(lines: list[dict] | None) -> int | None:
    if not lines:
        return None
    return sum(line["total"] for line in lines)


def _to_summary(row: ConversationSummaryRow) -> ConversationSummary:
    return ConversationSummary(
        id=row.conversation.id,
        channel=row.conversation.channel,
        client=row.client,
        last_message=row.last_message,
        status=derive_conversation_status(row.latest_quote),
        total=_quote_total(row.latest_quote.lines if row.latest_quote else None),
    )


# Filter tabs collapse the 3-way badge into 2 buckets — "needs attention"
# covers both held and attention, matching the design's two non-"all" tabs.
_STATUS_FILTERS = {
    "needs_attention": {"attention", "held"},
    "auto_sent": {"auto_sent"},
}


@router.get("", response_model=list[ConversationSummary])
async def list_conversations_endpoint(
    status_filter: str | None = Query(default=None, alias="status"),
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> list[ConversationSummary]:
    rows = await list_conversations(session, business.id)
    summaries = [_to_summary(row) for row in rows]
    allowed = _STATUS_FILTERS.get(status_filter) if status_filter else None
    if allowed is not None:
        summaries = [s for s in summaries if s.status in allowed]
    return summaries


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_endpoint(
    conversation_id: uuid.UUID,
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> ConversationDetail:
    thread = await get_conversation_thread(session, business.id, conversation_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    latest_quote = None
    if thread.latest_quote is not None and thread.latest_quote.lines:
        latest_quote = QuoteSummary(
            status=thread.latest_quote.status,
            lines=[PriceBreakdown.model_validate(line) for line in thread.latest_quote.lines],
            subtotal=_quote_total(thread.latest_quote.lines),
        )

    return ConversationDetail(
        id=thread.conversation.id,
        channel=thread.conversation.channel,
        client=thread.client,
        messages=thread.messages,
        latest_quote=latest_quote,
    )
