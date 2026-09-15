import uuid
from dataclasses import dataclass

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation, Message, Sender
from app.models.quote import Quote


async def get_business_by_whatsapp_phone_number_id(
    session: AsyncSession, phone_number_id: str
) -> Business | None:
    stmt = select(Business).where(Business.whatsapp_phone_number_id == phone_number_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_client(
    session: AsyncSession, business_id: uuid.UUID, phone_number: str, name: str | None = None
) -> Client:
    stmt = select(Client).where(
        Client.business_id == business_id, Client.phone_number == phone_number
    )
    result = await session.execute(stmt)
    client = result.scalar_one_or_none()
    if client is not None:
        return client

    client = Client(business_id=business_id, phone_number=phone_number, name=name)
    session.add(client)
    await session.commit()
    return client


async def get_conversation_by_id(
    session: AsyncSession, conversation_id: uuid.UUID
) -> Conversation | None:
    return await session.get(Conversation, conversation_id)


async def get_or_create_conversation(
    session: AsyncSession, business_id: uuid.UUID, client_id: uuid.UUID, channel: Channel
) -> Conversation:
    stmt = select(Conversation).where(
        Conversation.business_id == business_id,
        Conversation.client_id == client_id,
        Conversation.channel == channel,
    )
    result = await session.execute(stmt)
    conversation = result.scalar_one_or_none()
    if conversation is not None:
        return conversation

    conversation = Conversation(business_id=business_id, client_id=client_id, channel=channel)
    session.add(conversation)
    await session.commit()
    return conversation


async def get_conversation_history(
    session: AsyncSession, conversation_id: uuid.UUID
) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def message_exists(session: AsyncSession, whatsapp_message_id: str) -> bool:
    stmt = select(Message.id).where(Message.whatsapp_message_id == whatsapp_message_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def save_message(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    sender: Sender,
    content: str,
    whatsapp_message_id: str | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        whatsapp_message_id=whatsapp_message_id,
    )
    session.add(message)
    # Keeps the inbox list's sort order cheap to read (no per-row subquery).
    # synchronize_session=False: nothing in this function holds a loaded
    # Conversation to keep in sync, and it avoids an extra SELECT.
    await session.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(last_message_at=func.now())
        .execution_options(synchronize_session=False)
    )
    await session.commit()
    return message


async def get_conversation_for_business(
    session: AsyncSession, business_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation | None:
    """Like get_conversation_by_id, but 404-safe: None if it's someone else's."""
    stmt = select(Conversation).where(
        Conversation.id == conversation_id, Conversation.business_id == business_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_latest_quote(session: AsyncSession, conversation_id: uuid.UUID) -> Quote | None:
    stmt = (
        select(Quote)
        .where(Quote.conversation_id == conversation_id)
        .order_by(Quote.created_at.desc(), Quote.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def derive_conversation_status(latest_quote: Quote | None) -> str:
    """Inbox badge for a conversation, from its latest quote.

    No quote yet, or one with no priced lines (a clarifying question, an
    out-of-catalog item) -> "attention". Auto-sent quotes -> "auto_sent".
    Anything else (pending, or the not-yet-reachable approved/rejected)
    -> "held".
    """
    if latest_quote is None or not latest_quote.lines:
        return "attention"
    if latest_quote.status == "auto_sent":
        return "auto_sent"
    return "held"


@dataclass
class ConversationSummaryRow:
    conversation: Conversation
    client: Client
    last_message: Message | None
    latest_quote: Quote | None


async def list_conversations(
    session: AsyncSession, business_id: uuid.UUID
) -> list[ConversationSummaryRow]:
    """One conversation per row, newest thread first.

    Latest message and latest quote per conversation come from the same
    query (a window function each, not a subquery per row) rather than
    N+1 lookups.
    """
    message_order = (Message.created_at.desc(), Message.id.desc())
    message_row_number = func.row_number().over(
        partition_by=Message.conversation_id, order_by=message_order
    )
    message_rank = select(Message, message_row_number.label("rn")).subquery()
    latest_message = aliased(Message, message_rank)

    quote_order = (Quote.created_at.desc(), Quote.id.desc())
    quote_row_number = func.row_number().over(
        partition_by=Quote.conversation_id, order_by=quote_order
    )
    quote_rank = select(Quote, quote_row_number.label("rn")).subquery()
    latest_quote = aliased(Quote, quote_rank)

    stmt = (
        select(Conversation, Client, latest_message, latest_quote)
        .join(Client, Client.id == Conversation.client_id)
        .outerjoin(
            latest_message,
            (message_rank.c.conversation_id == Conversation.id) & (message_rank.c.rn == 1),
        )
        .outerjoin(
            latest_quote,
            (quote_rank.c.conversation_id == Conversation.id) & (quote_rank.c.rn == 1),
        )
        .where(Conversation.business_id == business_id)
        .order_by(Conversation.last_message_at.desc().nulls_last())
    )
    result = await session.execute(stmt)
    return [
        ConversationSummaryRow(conversation=conv, client=cl, last_message=msg, latest_quote=quote)
        for conv, cl, msg, quote in result.all()
    ]


@dataclass
class ConversationThread:
    conversation: Conversation
    client: Client
    messages: list[Message]
    latest_quote: Quote | None


async def get_conversation_thread(
    session: AsyncSession, business_id: uuid.UUID, conversation_id: uuid.UUID
) -> ConversationThread | None:
    conversation = await get_conversation_for_business(session, business_id, conversation_id)
    if conversation is None:
        return None

    client = await session.get(Client, conversation.client_id)
    messages = await get_conversation_history(session, conversation_id)
    latest_quote = await get_latest_quote(session, conversation_id)
    return ConversationThread(
        conversation=conversation, client=client, messages=messages, latest_quote=latest_quote
    )
