import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation
from app.models.order import Order, OrderStatus
from app.models.quote import Quote, QuoteStatus


async def _make_quote(session) -> tuple[Business, Conversation, Quote]:
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
    await session.flush()

    quote = Quote(
        conversation_id=conversation.id,
        draft_message="9500 DA",
        confidence=95,
        status=QuoteStatus.auto_sent,
        lines=[{"item_id": str(uuid.uuid4()), "total": 9500}],
    )
    session.add(quote)
    await session.commit()
    return business, conversation, quote


async def test_create_order_defaults_to_confirmed(session):
    business, conversation, quote = await _make_quote(session)

    order = Order(business_id=business.id, conversation_id=conversation.id, quote_id=quote.id)
    session.add(order)
    await session.commit()

    assert order.id is not None
    assert order.status == OrderStatus.confirmed


async def test_quote_id_unique_constraint(session):
    business, conversation, quote = await _make_quote(session)
    session.add(Order(business_id=business.id, conversation_id=conversation.id, quote_id=quote.id))
    await session.commit()

    with pytest.raises(IntegrityError):
        session.add(
            Order(business_id=business.id, conversation_id=conversation.id, quote_id=quote.id)
        )
        await session.commit()


async def test_status_rejects_invalid_value_at_db_level(session):
    business, conversation, quote = await _make_quote(session)

    with pytest.raises(IntegrityError):
        await session.execute(
            text(
                "INSERT INTO orders (business_id, conversation_id, quote_id, status) "
                "VALUES (:business_id, :conversation_id, :quote_id, 'not-a-status')"
            ),
            {"business_id": business.id, "conversation_id": conversation.id, "quote_id": quote.id},
        )
        await session.commit()
