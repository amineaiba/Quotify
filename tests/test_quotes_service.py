import uuid

import pytest

from app.core.exceptions import QuoteNotPending
from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation
from app.models.quote import HoldReason, QuoteStatus
from app.schemas.pricing import PriceBreakdown
from app.services.quotes import (
    approve_quote,
    get_quote_for_business,
    list_quotes,
    reject_quote,
    save_quote,
)

_LINE = PriceBreakdown(
    item_id=uuid.uuid4(), name="Flyer A5", unit="flyer",
    quantity=500, unit_price=19, applied_min_qty=500, total=9500,
)


async def _make_conversation(session, email: str | None = None) -> Conversation:
    business = Business(
        name="Atelier Print",
        email=email or f"owner-{uuid.uuid4()}@atelier.dz",
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


async def test_save_quote_auto_sent_with_lines(session):
    conversation = await _make_conversation(session)
    line = PriceBreakdown(
        item_id=uuid.uuid4(), name="Flyer A5", unit="flyer",
        quantity=500, unit_price=19, applied_min_qty=500, total=9500,
    )

    quote = await save_quote(
        session, conversation.id, "9500 DA", 92, [line], QuoteStatus.auto_sent
    )

    assert quote.status == QuoteStatus.auto_sent
    assert quote.hold_reason is None
    assert quote.lines == [line.model_dump(mode="json")]


async def test_save_quote_pending_without_lines(session):
    conversation = await _make_conversation(session)

    quote = await save_quote(
        session, conversation.id, "salut, ça va ?", 20, [], QuoteStatus.pending,
        hold_reason=HoldReason.low_confidence,
    )

    assert quote.status == QuoteStatus.pending
    assert quote.hold_reason == HoldReason.low_confidence
    assert quote.lines is None


async def test_list_quotes_scoped_to_business(session):
    conversation = await _make_conversation(session)
    other_conversation = await _make_conversation(session)
    await save_quote(session, conversation.id, "9500 DA", 92, [_LINE], QuoteStatus.pending)
    await save_quote(session, other_conversation.id, "1200 DA", 40, [], QuoteStatus.pending)

    rows = await list_quotes(session, conversation.business_id)

    assert len(rows) == 1
    assert rows[0].quote.draft_message == "9500 DA"
    assert rows[0].client.phone_number == "+213555000000"


async def test_list_quotes_filters_by_status(session):
    conversation = await _make_conversation(session)
    await save_quote(session, conversation.id, "pending one", 92, [_LINE], QuoteStatus.pending)
    await save_quote(session, conversation.id, "sent one", 95, [_LINE], QuoteStatus.auto_sent)

    rows = await list_quotes(session, conversation.business_id, status=QuoteStatus.pending)

    assert [r.quote.draft_message for r in rows] == ["pending one"]


async def test_get_quote_for_business_returns_none_for_other_business(session):
    conversation = await _make_conversation(session)
    other_conversation = await _make_conversation(session)
    quote = await save_quote(
        session, conversation.id, "9500 DA", 92, [_LINE], QuoteStatus.pending
    )

    row = await get_quote_for_business(session, other_conversation.business_id, quote.id)

    assert row is None


async def test_approve_quote_sets_final_message_and_status(session):
    conversation = await _make_conversation(session)
    quote = await save_quote(
        session, conversation.id, "9500 DA", 92, [_LINE], QuoteStatus.pending
    )

    approved = await approve_quote(session, quote, "9500 DA, livraison incluse")

    assert approved.status == QuoteStatus.approved
    assert approved.final_message == "9500 DA, livraison incluse"
    assert approved.reviewed_at is not None


async def test_approve_quote_raises_when_not_pending(session):
    conversation = await _make_conversation(session)
    quote = await save_quote(
        session, conversation.id, "9500 DA", 92, [_LINE], QuoteStatus.auto_sent
    )

    with pytest.raises(QuoteNotPending):
        await approve_quote(session, quote, "9500 DA")


async def test_reject_quote_sets_status_only(session):
    conversation = await _make_conversation(session)
    quote = await save_quote(
        session, conversation.id, "9500 DA", 92, [_LINE], QuoteStatus.pending
    )

    rejected = await reject_quote(session, quote)

    assert rejected.status == QuoteStatus.rejected
    assert rejected.final_message is None
    assert rejected.reviewed_at is not None


async def test_reject_quote_raises_when_not_pending(session):
    conversation = await _make_conversation(session)
    quote = await save_quote(session, conversation.id, "9500 DA", 92, [_LINE], QuoteStatus.rejected)

    with pytest.raises(QuoteNotPending):
        await reject_quote(session, quote)
