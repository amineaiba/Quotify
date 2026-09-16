import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NoConfirmableQuote, OrderAlreadyExists
from app.models.business import Client
from app.models.conversation import Conversation
from app.models.order import Order, OrderStatus
from app.models.quote import Quote, QuoteStatus
from app.services.conversation import get_latest_quote


async def confirm_order(session: AsyncSession, conversation_id: uuid.UUID) -> Order:
    """Creates an Order from the conversation's latest auto-sent, priced quote."""
    quote = await get_latest_quote(
        session, conversation_id, status=(QuoteStatus.auto_sent, QuoteStatus.approved)
    )
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


@dataclass
class OrderRow:
    order: Order
    conversation: Conversation
    client: Client
    quote: Quote


async def list_orders(session: AsyncSession, business_id: uuid.UUID) -> list[OrderRow]:
    stmt = (
        select(Order, Conversation, Client, Quote)
        .join(Conversation, Conversation.id == Order.conversation_id)
        .join(Client, Client.id == Conversation.client_id)
        .join(Quote, Quote.id == Order.quote_id)
        .where(Order.business_id == business_id)
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(stmt)
    return [
        OrderRow(order=o, conversation=c, client=cl, quote=q) for o, c, cl, q in result.all()
    ]


async def get_order_for_business(
    session: AsyncSession, business_id: uuid.UUID, order_id: uuid.UUID
) -> OrderRow | None:
    stmt = (
        select(Order, Conversation, Client, Quote)
        .join(Conversation, Conversation.id == Order.conversation_id)
        .join(Client, Client.id == Conversation.client_id)
        .join(Quote, Quote.id == Order.quote_id)
        .where(Order.business_id == business_id, Order.id == order_id)
    )
    result = await session.execute(stmt)
    row = result.first()
    if row is None:
        return None
    o, c, cl, q = row
    return OrderRow(order=o, conversation=c, client=cl, quote=q)
