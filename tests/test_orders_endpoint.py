from sqlalchemy import select

from app.models.business import Business
from app.models.conversation import Channel
from app.models.quote import QuoteStatus
from app.schemas.pricing import PriceBreakdown
from app.services.conversation import get_or_create_client, get_or_create_conversation
from app.services.orders import confirm_order
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


async def test_list_orders_requires_auth(client, session):
    response = await client.get("/api/v1/orders")
    assert response.status_code == 401


async def test_list_orders_returns_scoped_data(client, session):
    headers = await _auth_headers(client, "a@atelier.dz")
    business_id = await _business_id(session, "a@atelier.dz")
    await _auth_headers(client, "b@atelier.dz")
    other_id = await _business_id(session, "b@atelier.dz")

    cl = await get_or_create_client(session, business_id, "+213555000000", name="Amine")
    conv = await get_or_create_conversation(session, business_id, cl.id, Channel.whatsapp)
    await save_quote(session, conv.id, "devis", 95, [_LINE], QuoteStatus.auto_sent)
    await confirm_order(session, conv.id)

    other_cl = await get_or_create_client(session, other_id, "+213555000009", name="Stranger")
    other_conv = await get_or_create_conversation(session, other_id, other_cl.id, Channel.whatsapp)
    await save_quote(session, other_conv.id, "devis", 95, [_LINE], QuoteStatus.auto_sent)
    await confirm_order(session, other_conv.id)

    response = await client.get("/api/v1/orders", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client"]["name"] == "Amine"
    assert body[0]["status"] == "confirmed"
    assert body[0]["quote"]["subtotal"] == 14400


async def test_get_order_returns_detail(client, session):
    headers = await _auth_headers(client, "d@atelier.dz")
    business_id = await _business_id(session, "d@atelier.dz")
    cl = await get_or_create_client(session, business_id, "+213555000000", name="Amine")
    conv = await get_or_create_conversation(session, business_id, cl.id, Channel.whatsapp)
    await save_quote(session, conv.id, "devis", 95, [_LINE], QuoteStatus.auto_sent)
    order = await confirm_order(session, conv.id)

    response = await client.get(f"/api/v1/orders/{order.id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(order.id)
    assert body["conversation_id"] == str(conv.id)
    assert body["quote"]["lines"][0]["name"] == "Faïence 20x20"


async def test_get_order_from_another_business_returns_404(client, session):
    headers_a = await _auth_headers(client, "e@atelier.dz")
    await _auth_headers(client, "f@atelier.dz")
    business_b = await _business_id(session, "f@atelier.dz")
    cl = await get_or_create_client(session, business_b, "+213555000000", name="Stranger")
    conv = await get_or_create_conversation(session, business_b, cl.id, Channel.whatsapp)
    await save_quote(session, conv.id, "devis", 95, [_LINE], QuoteStatus.auto_sent)
    order = await confirm_order(session, conv.id)

    response = await client.get(f"/api/v1/orders/{order.id}", headers=headers_a)

    assert response.status_code == 404


async def test_get_unknown_order_returns_404(client, session):
    headers = await _auth_headers(client, "g@atelier.dz")
    response = await client.get(
        "/api/v1/orders/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404
