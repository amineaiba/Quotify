import pytest

from app.core.exceptions import NoConfirmableQuote, OrderAlreadyExists
from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation
from app.models.order import OrderStatus
from app.models.quote import Quote, QuoteStatus
from app.services.orders import confirm_order

_LINES = [
    {
        "item_id": "11111111-1111-1111-1111-111111111111",
        "name": "Flyer A5",
        "unit": "flyer",
        "quantity": 500,
        "unit_price": 19,
        "applied_min_qty": 500,
        "total": 9500,
    }
]


async def _make_conversation(session) -> Conversation:
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
    await session.flush()

    conversation = Conversation(
        business_id=business.id, client_id=client.id, channel=Channel.whatsapp
    )
    session.add(conversation)
    await session.commit()
    return conversation


async def _add_quote(session, conversation_id, quote_status, lines=None) -> Quote:
    quote = Quote(
        conversation_id=conversation_id,
        draft_message="9500 DA",
        confidence=95,
        status=quote_status,
        lines=lines,
    )
    session.add(quote)
    await session.commit()
    return quote


async def test_confirm_order_creates_order_from_latest_auto_sent_quote(session):
    conversation = await _make_conversation(session)
    quote = await _add_quote(session, conversation.id, QuoteStatus.auto_sent, _LINES)

    order = await confirm_order(session, conversation.id)

    assert order.quote_id == quote.id
    assert order.conversation_id == conversation.id
    assert order.business_id == conversation.business_id
    assert order.status == OrderStatus.confirmed


async def test_confirm_order_raises_when_no_quote_at_all(session):
    conversation = await _make_conversation(session)

    with pytest.raises(NoConfirmableQuote):
        await confirm_order(session, conversation.id)


async def test_confirm_order_raises_when_latest_quote_is_pending(session):
    conversation = await _make_conversation(session)
    await _add_quote(session, conversation.id, QuoteStatus.pending, _LINES)

    with pytest.raises(NoConfirmableQuote):
        await confirm_order(session, conversation.id)


async def test_confirm_order_raises_when_auto_sent_quote_has_no_lines(session):
    conversation = await _make_conversation(session)
    await _add_quote(session, conversation.id, QuoteStatus.auto_sent, lines=None)

    with pytest.raises(NoConfirmableQuote):
        await confirm_order(session, conversation.id)


async def test_confirm_order_raises_when_already_confirmed(session):
    conversation = await _make_conversation(session)
    await _add_quote(session, conversation.id, QuoteStatus.auto_sent, _LINES)
    await confirm_order(session, conversation.id)

    with pytest.raises(OrderAlreadyExists):
        await confirm_order(session, conversation.id)


async def test_confirm_order_creates_order_from_approved_quote(session):
    conversation = await _make_conversation(session)
    quote = await _add_quote(session, conversation.id, QuoteStatus.approved, _LINES)

    order = await confirm_order(session, conversation.id)

    assert order.quote_id == quote.id
    assert order.status == OrderStatus.confirmed


async def test_confirm_order_targets_latest_auto_sent_quote(session):
    """Documents the known gap: an older quote can't be confirmed once a
    newer one exists in the same conversation — see CLAUDE.local.md."""
    conversation = await _make_conversation(session)
    await _add_quote(session, conversation.id, QuoteStatus.auto_sent, _LINES)
    newer_quote = await _add_quote(session, conversation.id, QuoteStatus.auto_sent, _LINES)

    order = await confirm_order(session, conversation.id)

    assert order.quote_id == newer_quote.id
