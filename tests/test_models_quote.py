import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation
from app.models.quote import HoldReason, Quote, QuoteStatus


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


async def test_create_auto_sent_quote(session):
    conversation = await _make_conversation(session)

    quote = Quote(
        conversation_id=conversation.id,
        draft_message="9500 DA",
        confidence=92,
        status=QuoteStatus.auto_sent,
        lines=[{"item_id": str(uuid.uuid4()), "total": 9500}],
    )
    session.add(quote)
    await session.commit()

    assert quote.id is not None
    assert quote.hold_reason is None
    assert quote.final_message is None
    assert quote.reviewed_at is None


async def test_create_pending_quote_with_hold_reason(session):
    conversation = await _make_conversation(session)

    quote = Quote(
        conversation_id=conversation.id,
        draft_message="salut, ça va ?",
        confidence=20,
        status=QuoteStatus.pending,
        hold_reason=HoldReason.low_confidence,
    )
    session.add(quote)
    await session.commit()

    assert quote.status == QuoteStatus.pending
    assert quote.hold_reason == HoldReason.low_confidence
    assert quote.lines is None


async def test_status_rejects_invalid_value_at_db_level(session):
    conversation = await _make_conversation(session)

    with pytest.raises(IntegrityError):
        await session.execute(
            text(
                "INSERT INTO quotes (conversation_id, draft_message, status) "
                "VALUES (:conversation_id, 'hi', 'not-a-status')"
            ),
            {"conversation_id": conversation.id},
        )
        await session.commit()
