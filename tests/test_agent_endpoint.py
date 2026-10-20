from sqlalchemy import select

from app.agent.graph import MAX_TURNS
from app.models.business import Business
from app.models.conversation import Channel, Message, Sender
from app.schemas.agent import AgentReply
from app.services.conversation import get_or_create_client, get_or_create_conversation
from tests.conftest import (
    FLYER_ID,
    GraphFakeClient,
    graph_text_content,
    graph_tool_call_content,
    register_and_login,
    seed_flyer,
)

URL = "/api/v1/agent/messages"


async def _login(client, session, email="owner@atelier.dz"):
    token = await register_and_login(client, email)
    result = await session.execute(select(Business).where(Business.email == email))
    return result.scalar_one(), {"Authorization": f"Bearer {token}"}


async def test_messages_requires_auth(client, session):
    response = await client.post(URL, json={"message": "prix ?"})

    assert response.status_code == 401


async def test_messages_prices_item_and_returns_quote_ready(client, session, monkeypatch):
    business, headers = await _login(client, session)
    await seed_flyer(session, business)
    responses = [
        graph_tool_call_content("calc_price", {"item_id": str(FLYER_ID), "quantity": 500}),
        graph_text_content("500 flyers A5 recto-verso : 9500 DA."),
    ]
    client_double = GraphFakeClient(responses)
    monkeypatch.setattr("app.agent.graph.get_client", lambda: client_double)

    response = await client.post(
        URL, json={"message": "500 flyers A5 recto verso, chhal?"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "quote_ready"
    assert body["lines"][0]["total"] == 9500


async def test_messages_no_tool_calls_returns_needs_info(client, session, monkeypatch):
    responses = [graph_text_content("Quelle quantité voulez-vous ?")]
    client_double = GraphFakeClient(responses)
    monkeypatch.setattr("app.agent.graph.get_client", lambda: client_double)
    _, headers = await _login(client, session)

    response = await client.post(URL, json={"message": "svp le prix"}, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_info"
    assert body["lines"] == []


async def test_messages_rejects_empty_message(client, session):
    _, headers = await _login(client, session)

    response = await client.post(URL, json={"message": ""}, headers=headers)

    assert response.status_code == 422


async def test_messages_turn_limit_returns_503(client, session, monkeypatch):
    business, headers = await _login(client, session)
    await seed_flyer(session, business)
    always_calls = graph_tool_call_content(
        "calc_price", {"item_id": str(FLYER_ID), "quantity": 500}
    )
    responses = [always_calls] * MAX_TURNS
    client_double = GraphFakeClient(responses)
    monkeypatch.setattr("app.agent.graph.get_client", lambda: client_double)

    response = await client.post(URL, json={"message": "500 flyers"}, headers=headers)

    assert response.status_code == 503


async def test_messages_unknown_conversation_id_returns_404(client, session):
    _, headers = await _login(client, session)

    response = await client.post(
        URL,
        json={"message": "500 flyers", "conversation_id": "11111111-1111-1111-1111-111111111111"},
        headers=headers,
    )

    assert response.status_code == 404


async def test_messages_with_conversation_id_saves_turns_and_uses_history(
    client, session, monkeypatch
):
    business, headers = await _login(client, session)
    wa_client = await get_or_create_client(session, business.id, "+213555000000")
    conversation = await get_or_create_conversation(
        session, business.id, wa_client.id, Channel.whatsapp
    )
    await session.commit()

    seen_history = {}

    async def fake_run_agent(session, history, conversation_id=None, business_id=None):
        seen_history["value"] = history
        seen_history["business_id"] = business_id
        return AgentReply(status="needs_info", message="quelle quantité ?", lines=[])

    monkeypatch.setattr("app.routers.agent.run_agent", fake_run_agent)

    response = await client.post(
        URL,
        json={"message": "prix des flyers ?", "conversation_id": str(conversation.id)},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "quelle quantité ?"

    result = await session.execute(select(Message).order_by(Message.created_at))
    saved = result.scalars().all()
    assert [(m.sender, m.content) for m in saved] == [
        (Sender.client, "prix des flyers ?"),
        (Sender.agent, "quelle quantité ?"),
    ]
    assert [c.parts[0].text for c in seen_history["value"]] == ["prix des flyers ?"]
    assert seen_history["business_id"] == business.id


async def test_messages_second_turn_includes_first_in_history(client, session, monkeypatch):
    business, headers = await _login(client, session)
    wa_client = await get_or_create_client(session, business.id, "+213555000000")
    conversation = await get_or_create_conversation(
        session, business.id, wa_client.id, Channel.whatsapp
    )
    await session.commit()

    seen_history = {}

    async def fake_run_agent(session, history, conversation_id=None, business_id=None):
        seen_history["value"] = history
        return AgentReply(status="needs_info", message="ok", lines=[])

    monkeypatch.setattr("app.routers.agent.run_agent", fake_run_agent)

    await client.post(
        URL,
        json={"message": "prix des flyers ?", "conversation_id": str(conversation.id)},
        headers=headers,
    )
    await client.post(
        URL,
        json={"message": "500 pièces", "conversation_id": str(conversation.id)},
        headers=headers,
    )

    history = seen_history["value"]
    assert [c.parts[0].text for c in history] == [
        "prix des flyers ?",
        "ok",
        "500 pièces",
    ]
    assert [c.role for c in history] == ["user", "model", "user"]


async def test_messages_other_business_conversation_returns_404(client, session):
    owner, _ = await _login(client, session, "a@atelier.dz")
    _, other_headers = await _login(client, session, "b@atelier.dz")
    wa_client = await get_or_create_client(session, owner.id, "+213555000000")
    conversation = await get_or_create_conversation(
        session, owner.id, wa_client.id, Channel.whatsapp
    )
    await session.commit()

    response = await client.post(
        URL,
        json={"message": "salam", "conversation_id": str(conversation.id)},
        headers=other_headers,
    )

    assert response.status_code == 404
