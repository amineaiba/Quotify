import uuid

from app.agent.tools import dispatch
from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation
from app.models.quote import Quote, QuoteStatus
from tests.conftest import FLYER_ID, seed_flyer


async def test_dispatch_calc_price_success(session):
    await seed_flyer(session)

    result = await dispatch(session, "calc_price", {"item_id": str(FLYER_ID), "quantity": 500})

    assert result["total"] == 9500
    assert result["unit_price"] == 19


async def test_dispatch_calc_price_below_minimum_returns_error(session):
    await seed_flyer(session)

    result = await dispatch(session, "calc_price", {"item_id": str(FLYER_ID), "quantity": 50})

    assert result == {"error": "BelowMinimumQuantity", "min_qty": 100}


async def test_dispatch_calc_price_unknown_item_returns_error(session):
    unknown_id = str(uuid.uuid4())

    result = await dispatch(session, "calc_price", {"item_id": unknown_id, "quantity": 500})

    assert result == {"error": "ItemNotFound", "item_id": unknown_id}


async def test_dispatch_unknown_tool_returns_error(session):
    result = await dispatch(session, "not_a_real_tool", {})

    assert result == {"error": "UnknownTool", "name": "not_a_real_tool"}


async def _make_conversation_with_auto_sent_quote(session) -> Conversation:
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
    return conversation


async def test_dispatch_confirm_order_creates_order(session):
    conversation = await _make_conversation_with_auto_sent_quote(session)

    result = await dispatch(session, "confirm_order", {}, conversation.id)

    assert "order_id" in result
    assert result["status"] == "confirmed"


async def test_dispatch_confirm_order_no_quote_returns_error(session):
    result = await dispatch(session, "confirm_order", {}, uuid.uuid4())

    assert result == {"error": "NoConfirmableQuote"}


async def test_dispatch_confirm_order_without_conversation_id_returns_error(session):
    result = await dispatch(session, "confirm_order", {})

    assert result == {"error": "NoConfirmableQuote"}


async def test_dispatch_confirm_order_already_confirmed_returns_error(session):
    conversation = await _make_conversation_with_auto_sent_quote(session)
    await dispatch(session, "confirm_order", {}, conversation.id)

    result = await dispatch(session, "confirm_order", {}, conversation.id)

    assert result == {"error": "AlreadyConfirmed"}
