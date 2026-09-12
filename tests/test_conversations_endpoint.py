from sqlalchemy import select

from app.models.business import Business
from app.models.conversation import Channel, Sender
from app.models.quote import QuoteStatus
from app.schemas.pricing import PriceBreakdown
from app.services.conversation import get_or_create_client, get_or_create_conversation, save_message
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


async def test_list_conversations_requires_auth(client, session):
    response = await client.get("/api/v1/conversations")
    assert response.status_code == 401


async def test_list_conversations_returns_scoped_data(client, session):
    headers = await _auth_headers(client, "a@atelier.dz")
    business_id = await _business_id(session, "a@atelier.dz")
    await _auth_headers(client, "b@atelier.dz")
    other_id = await _business_id(session, "b@atelier.dz")

    cl = await get_or_create_client(session, business_id, "+213555000000", name="Amine")
    conv = await get_or_create_conversation(session, business_id, cl.id, Channel.whatsapp)
    await save_message(session, conv.id, Sender.client, "salam")
    await save_quote(session, conv.id, "devis", 95, [_LINE], QuoteStatus.auto_sent)

    other_cl = await get_or_create_client(session, other_id, "+213555000009", name="Stranger")
    await get_or_create_conversation(session, other_id, other_cl.id, Channel.whatsapp)

    response = await client.get("/api/v1/conversations", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    row = body[0]
    assert row["client"]["name"] == "Amine"
    assert row["last_message"]["content"] == "salam"
    assert row["status"] == "auto_sent"
    assert row["total"] == 14400


async def test_list_conversations_filters_by_status(client, session):
    headers = await _auth_headers(client, "c@atelier.dz")
    business_id = await _business_id(session, "c@atelier.dz")

    sent_client = await get_or_create_client(session, business_id, "+213555000001", name="Sent")
    sent_conv = await get_or_create_conversation(
        session, business_id, sent_client.id, Channel.whatsapp
    )
    await save_message(session, sent_conv.id, Sender.client, "salam")
    await save_quote(session, sent_conv.id, "devis", 95, [_LINE], QuoteStatus.auto_sent)

    waiting_client = await get_or_create_client(
        session, business_id, "+213555000002", name="Waiting"
    )
    waiting_conv = await get_or_create_conversation(
        session, business_id, waiting_client.id, Channel.whatsapp
    )
    await save_message(session, waiting_conv.id, Sender.client, "bonjour")

    response = await client.get(
        "/api/v1/conversations", params={"status": "needs_attention"}, headers=headers
    )

    assert response.status_code == 200
    names = [row["client"]["name"] for row in response.json()]
    assert names == ["Waiting"]


async def test_get_conversation_returns_thread(client, session):
    headers = await _auth_headers(client, "d@atelier.dz")
    business_id = await _business_id(session, "d@atelier.dz")
    cl = await get_or_create_client(session, business_id, "+213555000000", name="Amine")
    conv = await get_or_create_conversation(session, business_id, cl.id, Channel.whatsapp)
    await save_message(session, conv.id, Sender.client, "salam")
    await save_message(session, conv.id, Sender.agent, "bonjour")
    await save_quote(session, conv.id, "devis", 95, [_LINE], QuoteStatus.auto_sent)

    response = await client.get(f"/api/v1/conversations/{conv.id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert [m["content"] for m in body["messages"]] == ["salam", "bonjour"]
    assert body["latest_quote"]["subtotal"] == 14400
    assert body["latest_quote"]["lines"][0]["name"] == "Faïence 20x20"


async def test_get_conversation_from_another_business_returns_404(client, session):
    headers_a = await _auth_headers(client, "e@atelier.dz")
    await _auth_headers(client, "f@atelier.dz")
    business_b = await _business_id(session, "f@atelier.dz")
    cl = await get_or_create_client(session, business_b, "+213555000000", name="Stranger")
    conv = await get_or_create_conversation(session, business_b, cl.id, Channel.whatsapp)

    response = await client.get(f"/api/v1/conversations/{conv.id}", headers=headers_a)

    assert response.status_code == 404


async def test_get_unknown_conversation_returns_404(client, session):
    headers = await _auth_headers(client, "g@atelier.dz")
    response = await client.get(
        "/api/v1/conversations/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404
