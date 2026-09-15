import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NoConfirmableQuote, OrderAlreadyExists
from app.models.conversation import Conversation
from app.models.order import Order, OrderStatus
from app.models.quote import QuoteStatus
from app.services.conversation import get_latest_quote


async def confirm_order(session: AsyncSession, conversation_id: uuid.UUID) -> Order:
    """Creates an Order from the conversation's latest auto-sent, priced quote."""
    quote = await get_latest_quote(session, conversation_id, status=QuoteStatus.auto_sent)
    if quote is None or not quote.lines:
        raise NoConfirmableQuote()

    existing = await session.execute(select(Order).where(Order.quote_id == quote.id))
    if existing.scalar_one_or_none() is not None:
        raise OrderAlreadyExists()

    conversation = await session.get(Conversation, conversation_id)
    order = Order(
        business_id=conversation.business_id,
        conversation_id=conversation_id,
        quote_id=quote.id,
        status=OrderStatus.confirmed,
    )
    session.add(order)
    await session.commit()
    return order
