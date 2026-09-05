from app.models.conversation import Channel, Sender
from app.services.conversation import (
    get_or_create_client,
    get_or_create_conversation,
    message_exists,
    save_message,
)
from tests.conftest import make_business


async def test_get_or_create_client_is_idempotent(session):
    business = await make_business(session)

    first = await get_or_create_client(session, business.id, "+213555000000", name="Yacine")
    second = await get_or_create_client(session, business.id, "+213555000000", name="Yacine")

    assert first.id == second.id


async def test_get_or_create_conversation_is_idempotent(session):
    business = await make_business(session)
    client = await get_or_create_client(session, business.id, "+213555000000")

    first = await get_or_create_conversation(session, business.id, client.id, Channel.whatsapp)
    second = await get_or_create_conversation(session, business.id, client.id, Channel.whatsapp)

    assert first.id == second.id


async def test_message_exists_true_only_after_save(session):
    business = await make_business(session)
    client = await get_or_create_client(session, business.id, "+213555000000")
    conversation = await get_or_create_conversation(
        session, business.id, client.id, Channel.whatsapp
    )

    assert await message_exists(session, "wamid.1") is False

    await save_message(session, conversation.id, Sender.client, "hi", whatsapp_message_id="wamid.1")

    assert await message_exists(session, "wamid.1") is True
