import uuid

from sqlalchemy.ext.asyncio import AsyncSession

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
