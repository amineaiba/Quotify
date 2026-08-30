import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation, Message, Sender


async def _make_client(session) -> Client:
    business = Business(
        name="Atelier Print",
        email="owner@atelier.dz",
        hashed_password="hashed",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    client = Client(phone_number="+213555000000", name="Yacine")
    business.clients.append(client)
    session.add(business)
    await session.commit()
    return client


async def test_create_conversation_and_messages(session):
    client = await _make_client(session)

    conversation = Conversation(
        business_id=client.business_id, client_id=client.id, channel=Channel.whatsapp
    )
    conversation.messages.append(Message(sender=Sender.client, content="chhal 500 flyers?"))
    conversation.messages.append(Message(sender=Sender.agent, content="9500 DA"))
    session.add(conversation)
    await session.commit()

    assert conversation.id is not None
    assert conversation.channel == Channel.whatsapp
    assert [m.sender for m in conversation.messages] == [Sender.client, Sender.agent]


async def test_messages_ordered_by_created_at(session):
    client = await _make_client(session)
    conversation = Conversation(
        business_id=client.business_id, client_id=client.id, channel=Channel.whatsapp
    )
    session.add(conversation)
    await session.flush()

    session.add(Message(conversation_id=conversation.id, sender=Sender.client, content="first"))
    await session.commit()
    session.add(Message(conversation_id=conversation.id, sender=Sender.agent, content="second"))
    await session.commit()

    await session.refresh(conversation, attribute_names=["messages"])
    assert [m.content for m in conversation.messages] == ["first", "second"]


async def test_channel_rejects_invalid_value_at_db_level(session):
    client = await _make_client(session)

    with pytest.raises(IntegrityError):
        await session.execute(
            text(
                "INSERT INTO conversations (business_id, client_id, channel) "
                "VALUES (:business_id, :client_id, 'carrier-pigeon')"
            ),
            {"business_id": client.business_id, "client_id": client.id},
        )
        await session.commit()


async def test_sender_rejects_invalid_value_at_db_level(session):
    client = await _make_client(session)
    conversation = Conversation(
        business_id=client.business_id, client_id=client.id, channel=Channel.whatsapp
    )
    session.add(conversation)
    await session.commit()

    with pytest.raises(IntegrityError):
        await session.execute(
            text(
                "INSERT INTO messages (conversation_id, sender, content) "
                "VALUES (:conversation_id, 'ghost', 'boo')"
            ),
            {"conversation_id": conversation.id},
        )
        await session.commit()
