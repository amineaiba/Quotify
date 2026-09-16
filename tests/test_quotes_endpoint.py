from sqlalchemy import select

from app.models.business import Business
from app.models.conversation import Channel, Message, Sender
from app.models.quote import QuoteStatus
from app.schemas.pricing import PriceBreakdown
from app.services.conversation import get_or_create_client, get_or_create_conversation
from app.services.quotes import save_quote
from tests.conftest import register_and_login

_LINE = PriceBreakdown(
    item_id="11111111-1111-1111-1111-111111111111", name="Faïence 20x20", unit="m2",
    quantity=6, unit_price=2400, applied_min_qty=1, total=14400,
)


async def _auth_headers(client, email="owner@atelier.dz") -> dict:
    token = await register_and_login(client, email)
    return {"Authorization": f"Bearer {token}"}


async def _business_id(session, email: str):
    result = await session.execute(select(Business).where(Business.email == email))
    return result.scalar_one().id


async def test_list_quotes_requires_auth(client, session):
    response = await client.get("/api/v1/quotes")
    assert response.status_code == 401


async def test_list_quotes_scoped_and_filterable(client, session):
    headers = await _auth_headers(client, "a@atelier.dz")
    business_id = await _business_id(session, "a@atelier.dz")
    await _auth_headers(client, "b@atelier.dz")
    other_id = await _business_id(session, "b@atelier.dz")

    cl = await get_or_create_client(session, business_id, "+213555000000", name="Amine")
    conv = await get_or_create_conversation(session, business_id, cl.id, Channel.whatsapp)
    await save_quote(session, conv.id, "9500 DA", 92, [_LINE], QuoteStatus.pending)
    await save_quote(session, conv.id, "already sent", 95, [_LINE], QuoteStatus.auto_sent)

    other_cl = await get_or_create_client(session, other_id, "+213555000009", name="Stranger")
    other_conv = await get_or_create_conversation(session, other_id, other_cl.id, Channel.whatsapp)
    await save_quote(session, other_conv.id, "not mine", 90, [_LINE], QuoteStatus.pending)

    response = await client.get("/api/v1/quotes", headers=headers)
    assert response.status_code == 200
    assert {q["draft_message"] for q in response.json()} == {"9500 DA", "already sent"}

    filtered = await client.get("/api/v1/quotes", params={"status": "pending"}, headers=headers)
    assert filtered.status_code == 200
    assert [q["draft_message"] for q in filtered.json()] == ["9500 DA"]


async def test_list_quotes_rejects_unknown_status(client, session):
    headers = await _auth_headers(client, "z@atelier.dz")
    response = await client.get(
        "/api/v1/quotes", params={"status": "not_a_status"}, headers=headers
    )
    assert response.status_code == 422


async def test_approve_quote_sends_message_and_updates_status(client, session, monkeypatch):
    headers = await _auth_headers(client, "c@atelier.dz")
    business_id = await _business_id(session, "c@atelier.dz")
    cl = await get_or_create_client(session, business_id, "+213555000000", name="Amine")
    conv = await get_or_create_conversation(session, business_id, cl.id, Channel.whatsapp)
    quote = await save_quote(session, conv.id, "9500 DA", 60, [_LINE], QuoteStatus.pending)

    sent = {}

    async def fake_send_message(phone_number_id, to, text):
        sent["phone_number_id"] = phone_number_id
        sent["to"] = to
        sent["text"] = text

    monkeypatch.setattr("app.routers.quotes.send_message", fake_send_message)

    response = await client.post(
        f"/api/v1/quotes/{quote.id}/approve",
        json={"message": "9500 DA, livraison incluse"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["final_message"] == "9500 DA, livraison incluse"
    assert sent == {
        "phone_number_id": None,
        "to": "+213555000000",
        "text": "9500 DA, livraison incluse",
    }

    messages = await session.execute(
        select(Message).where(Message.conversation_id == conv.id, Message.sender == Sender.agent)
    )
    saved = messages.scalars().one()
    assert saved.content == "9500 DA, livraison incluse"


async def test_approve_quote_returns_409_when_not_pending(client, session, monkeypatch):
    headers = await _auth_headers(client, "d@atelier.dz")
    business_id = await _business_id(session, "d@atelier.dz")
    cl = await get_or_create_client(session, business_id, "+213555000000", name="Amine")
    conv = await get_or_create_conversation(session, business_id, cl.id, Channel.whatsapp)
    quote = await save_quote(session, conv.id, "9500 DA", 95, [_LINE], QuoteStatus.auto_sent)

    async def fake_send_message(phone_number_id, to, text):
        pass

    monkeypatch.setattr("app.routers.quotes.send_message", fake_send_message)

    response = await client.post(
        f"/api/v1/quotes/{quote.id}/approve", json={"message": "9500 DA"}, headers=headers
    )

    assert response.status_code == 409


async def test_approve_unknown_quote_returns_404(client, session):
    headers = await _auth_headers(client, "e@atelier.dz")
    response = await client.post(
        "/api/v1/quotes/00000000-0000-0000-0000-000000000000/approve",
        json={"message": "hi"},
        headers=headers,
    )
    assert response.status_code == 404


async def test_approve_quote_from_another_business_returns_404(client, session):
    headers_a = await _auth_headers(client, "f@atelier.dz")
    await _auth_headers(client, "g@atelier.dz")
    business_b = await _business_id(session, "g@atelier.dz")
    cl = await get_or_create_client(session, business_b, "+213555000000", name="Stranger")
    conv = await get_or_create_conversation(session, business_b, cl.id, Channel.whatsapp)
    quote = await save_quote(session, conv.id, "9500 DA", 60, [_LINE], QuoteStatus.pending)

    response = await client.post(
        f"/api/v1/quotes/{quote.id}/approve", json={"message": "hi"}, headers=headers_a
    )

    assert response.status_code == 404


async def test_reject_quote_sets_status_and_sends_nothing(client, session, monkeypatch):
    headers = await _auth_headers(client, "h@atelier.dz")
    business_id = await _business_id(session, "h@atelier.dz")
    cl = await get_or_create_client(session, business_id, "+213555000000", name="Amine")
    conv = await get_or_create_conversation(session, business_id, cl.id, Channel.whatsapp)
    quote = await save_quote(session, conv.id, "9500 DA", 40, [_LINE], QuoteStatus.pending)

    sent = {}

    async def fake_send_message(phone_number_id, to, text):
        sent["called"] = True

    monkeypatch.setattr("app.routers.quotes.send_message", fake_send_message)

    response = await client.post(f"/api/v1/quotes/{quote.id}/reject", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert "called" not in sent

    messages = await session.execute(
        select(Message).where(Message.conversation_id == conv.id)
    )
    assert messages.scalars().all() == []


async def test_reject_quote_returns_409_when_not_pending(client, session):
    headers = await _auth_headers(client, "i@atelier.dz")
    business_id = await _business_id(session, "i@atelier.dz")
    cl = await get_or_create_client(session, business_id, "+213555000000", name="Amine")
    conv = await get_or_create_conversation(session, business_id, cl.id, Channel.whatsapp)
    quote = await save_quote(session, conv.id, "9500 DA", 40, [_LINE], QuoteStatus.rejected)

    response = await client.post(f"/api/v1/quotes/{quote.id}/reject", headers=headers)

    assert response.status_code == 409
