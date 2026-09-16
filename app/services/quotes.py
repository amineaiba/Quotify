import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import QuoteNotPending
from app.models.business import Client
from app.models.conversation import Conversation
from app.models.quote import HoldReason, Quote, QuoteStatus
from app.schemas.pricing import PriceBreakdown


async def save_quote(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    draft_message: str,
    confidence: int | None,
    lines: list[PriceBreakdown],
    status: QuoteStatus,
    hold_reason: HoldReason | None = None,
) -> Quote:
    quote = Quote(
        conversation_id=conversation_id,
        draft_message=draft_message,
        confidence=confidence,
        lines=[line.model_dump(mode="json") for line in lines] or None,
        status=status,
        hold_reason=hold_reason,
    )
    session.add(quote)
    await session.commit()
    return quote


@dataclass
class QuoteRow:
    quote: Quote
    conversation: Conversation
    client: Client


def _quote_rows_query(business_id: uuid.UUID):
    return (
        select(Quote, Conversation, Client)
        .join(Conversation, Conversation.id == Quote.conversation_id)
        .join(Client, Client.id == Conversation.client_id)
        .where(Conversation.business_id == business_id)
    )


async def list_quotes(
    session: AsyncSession, business_id: uuid.UUID, status: QuoteStatus | None = None
) -> list[QuoteRow]:
    stmt = _quote_rows_query(business_id).order_by(Quote.created_at.desc(), Quote.id.desc())
    if status is not None:
        stmt = stmt.where(Quote.status == status)
    result = await session.execute(stmt)
    return [QuoteRow(quote=q, conversation=c, client=cl) for q, c, cl in result.all()]


async def get_quote_for_business(
    session: AsyncSession, business_id: uuid.UUID, quote_id: uuid.UUID
) -> QuoteRow | None:
    stmt = _quote_rows_query(business_id).where(Quote.id == quote_id)
    result = await session.execute(stmt)
    row = result.first()
    if row is None:
        return None
    q, c, cl = row
    return QuoteRow(quote=q, conversation=c, client=cl)


async def approve_quote(session: AsyncSession, quote: Quote, message: str) -> Quote:
    if quote.status != QuoteStatus.pending:
        raise QuoteNotPending()
    quote.final_message = message
    quote.status = QuoteStatus.approved
    quote.reviewed_at = datetime.now(UTC)
    await session.commit()
    return quote


async def reject_quote(session: AsyncSession, quote: Quote) -> Quote:
    if quote.status != QuoteStatus.pending:
        raise QuoteNotPending()
    quote.status = QuoteStatus.rejected
    quote.reviewed_at = datetime.now(UTC)
    await session.commit()
    return quote
