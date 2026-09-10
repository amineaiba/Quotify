import uuid

from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation
from app.models.quote import HoldReason, QuoteStatus
from app.schemas.pricing import PriceBreakdown
from app.services.quotes import save_quote


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
