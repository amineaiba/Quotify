import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation, Message, Sender


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
