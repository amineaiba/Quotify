import uuid

from app.models.conversation import Channel, Sender
from app.models.quote import Quote, QuoteStatus
from app.schemas.pricing import PriceBreakdown
from app.services.conversation import (
    derive_conversation_status,
    get_conversation_by_id,
    get_conversation_for_business,
    get_conversation_history,
    get_conversation_thread,
    get_latest_quote,
    get_or_create_client,
    get_or_create_conversation,
    list_conversations,
    message_exists,
    save_message,
)
from app.services.quotes import save_quote
from tests.conftest import make_business

_LINE = PriceBreakdown(
    item_id=uuid.uuid4(), name="Faïence 20x20", unit="m2",
    quantity=6, unit_price=2400, applied_min_qty=1, total=14400,
)


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


async def test_get_conversation_by_id_returns_none_when_missing(session):
    assert await get_conversation_by_id(session, uuid.uuid4()) is None


async def test_get_conversation_by_id_returns_conversation(session):
    business = await make_business(session)
    client = await get_or_create_client(session, business.id, "+213555000000")
    conversation = await get_or_create_conversation(
        session, business.id, client.id, Channel.whatsapp
    )

    found = await get_conversation_by_id(session, conversation.id)

    assert found.id == conversation.id


async def test_get_conversation_history_returns_messages_in_order(session):
    business = await make_business(session)
    client = await get_or_create_client(session, business.id, "+213555000000")
    conversation = await get_or_create_conversation(
        session, business.id, client.id, Channel.whatsapp
    )
    await save_message(session, conversation.id, Sender.client, "salut")
    await save_message(session, conversation.id, Sender.agent, "bonjour")

    history = await get_conversation_history(session, conversation.id)

    assert [m.content for m in history] == ["salut", "bonjour"]


async def test_save_message_bumps_conversation_last_message_at(session):
    business = await make_business(session)
    client = await get_or_create_client(session, business.id, "+213555000000")
    conversation = await get_or_create_conversation(
        session, business.id, client.id, Channel.whatsapp
    )
    assert conversation.last_message_at is None

    await save_message(session, conversation.id, Sender.client, "salut")

    await session.refresh(conversation)
    assert conversation.last_message_at is not None


async def test_get_conversation_for_business_scopes_to_owner(session):
    owner = await make_business(session)
    stranger = await make_business(session)
    client = await get_or_create_client(session, owner.id, "+213555000000")
    conversation = await get_or_create_conversation(session, owner.id, client.id, Channel.whatsapp)

    assert await get_conversation_for_business(session, owner.id, conversation.id) is not None
    assert await get_conversation_for_business(session, stranger.id, conversation.id) is None


async def test_get_latest_quote_returns_most_recent(session):
    business = await make_business(session)
    client = await get_or_create_client(session, business.id, "+213555000000")
    conversation = await get_or_create_conversation(
        session, business.id, client.id, Channel.whatsapp
    )
    assert await get_latest_quote(session, conversation.id) is None

    await save_quote(session, conversation.id, "first draft", 80, [], QuoteStatus.pending)
    second = await save_quote(
        session, conversation.id, "second draft", 90, [_LINE], QuoteStatus.auto_sent
    )

    latest = await get_latest_quote(session, conversation.id)
    assert latest.id == second.id


def test_derive_conversation_status_maps_quote_to_badge():
    line_dump = [_LINE.model_dump(mode="json")]

    def quote(status, lines):
        return Quote(conversation_id=uuid.uuid4(), draft_message="x", status=status, lines=lines)

    assert derive_conversation_status(None) == "attention"
    assert derive_conversation_status(quote(QuoteStatus.pending, None)) == "attention"
    assert derive_conversation_status(quote(QuoteStatus.pending, [])) == "attention"
    assert derive_conversation_status(quote(QuoteStatus.auto_sent, line_dump)) == "auto_sent"
    assert derive_conversation_status(quote(QuoteStatus.pending, line_dump)) == "held"
    assert derive_conversation_status(quote(QuoteStatus.approved, line_dump)) == "held"


async def test_list_conversations_scoped_and_ordered(session):
    owner = await make_business(session)
    stranger = await make_business(session)
    await get_or_create_client(session, stranger.id, "+213000000000")

    client_a = await get_or_create_client(session, owner.id, "+213555000001", name="Amine")
    conv_a = await get_or_create_conversation(session, owner.id, client_a.id, Channel.whatsapp)
    await save_message(session, conv_a.id, Sender.client, "salam")

    client_b = await get_or_create_client(session, owner.id, "+213555000002", name="Sofiane")
    conv_b = await get_or_create_conversation(session, owner.id, client_b.id, Channel.whatsapp)
    await save_message(session, conv_b.id, Sender.client, "bonjour")
    await save_quote(session, conv_b.id, "devis", 95, [_LINE], QuoteStatus.auto_sent)

    rows = await list_conversations(session, owner.id)

    assert [r.conversation.id for r in rows] == [conv_b.id, conv_a.id]
    assert rows[0].client.name == "Sofiane"
    assert rows[0].last_message.content == "bonjour"
    assert rows[0].latest_quote.status == QuoteStatus.auto_sent
    assert rows[1].latest_quote is None


async def test_get_conversation_thread_returns_none_for_stranger(session):
    owner = await make_business(session)
    stranger = await make_business(session)
    client = await get_or_create_client(session, owner.id, "+213555000000")
    conversation = await get_or_create_conversation(session, owner.id, client.id, Channel.whatsapp)

    assert await get_conversation_thread(session, stranger.id, conversation.id) is None


async def test_get_conversation_thread_returns_messages_and_latest_quote(session):
    business = await make_business(session)
    client = await get_or_create_client(session, business.id, "+213555000000", name="Amine")
    conversation = await get_or_create_conversation(
        session, business.id, client.id, Channel.whatsapp
    )
    await save_message(session, conversation.id, Sender.client, "salam")
    await save_quote(session, conversation.id, "devis", 95, [_LINE], QuoteStatus.auto_sent)

    thread = await get_conversation_thread(session, business.id, conversation.id)

    assert thread.client.name == "Amine"
    assert [m.content for m in thread.messages] == ["salam"]
    assert thread.latest_quote.status == QuoteStatus.auto_sent
