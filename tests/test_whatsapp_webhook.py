import hashlib
import hmac
import json

from sqlalchemy import select

from app.core.config import get_settings
from app.models.conversation import Channel, Message, Sender
from app.models.quote import HoldReason, Quote, QuoteStatus
from app.schemas.agent import AgentReply
from app.services.conversation import get_or_create_client, get_or_create_conversation, save_message
from tests.conftest import make_business

PHONE_NUMBER_ID = "123456"


def _payload(message_id: str = "wamid.1", text: str = "chhal 500 flyers?") -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": PHONE_NUMBER_ID},
                            "contacts": [{"profile": {"name": "Yacine"}, "wa_id": "213555000000"}],
                            "messages": [
                                {
                                    "id": message_id,
                                    "from": "213555000000",
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }


def _sign(body: bytes) -> str:
    secret = get_settings().meta_app_secret
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


async def test_get_handshake_returns_challenge_on_matching_token(client):
    token = get_settings().meta_verify_token
    response = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": token, "hub.challenge": "abc123"},
    )
    assert response.status_code == 200
    assert response.text == "abc123"


async def test_get_handshake_rejects_wrong_token(client):
    response = await client.get(
        "/api/v1/webhooks/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "abc123"},
    )
    assert response.status_code == 403


async def test_post_rejects_bad_signature(client, session):
    await make_business(session, whatsapp_phone_number_id=PHONE_NUMBER_ID)
    body_bytes = json.dumps(_payload()).encode()

    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=body_bytes,
        headers={"X-Hub-Signature-256": "sha256=deadbeef", "Content-Type": "application/json"},
    )

    assert response.status_code == 401
    result = await session.execute(select(Message))
    assert result.scalars().all() == []


async def test_post_saves_message_and_schedules_reply(client, session, monkeypatch):
    await make_business(session, whatsapp_phone_number_id=PHONE_NUMBER_ID)

    sent = {}

    async def fake_run_agent(session, history):
        return AgentReply(status="quote_ready", message="9500 DA", lines=[], confidence=95)

    async def fake_send_message(phone_number_id, to, text):
        sent["phone_number_id"] = phone_number_id
        sent["to"] = to
        sent["text"] = text

    monkeypatch.setattr("app.routers.webhooks.whatsapp.run_agent", fake_run_agent)
    monkeypatch.setattr("app.routers.webhooks.whatsapp.send_message", fake_send_message)

    body_bytes = json.dumps(_payload()).encode()
    response = await client.post(
        "/api/v1/webhooks/whatsapp",
        content=body_bytes,
        headers={
            "X-Hub-Signature-256": _sign(body_bytes),
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200

    result = await session.execute(select(Message).order_by(Message.created_at))
    messages = result.scalars().all()
    assert [m.sender for m in messages] == [Sender.client, Sender.agent]
    assert messages[0].content == "chhal 500 flyers?"
    assert messages[1].content == "9500 DA"

    assert sent == {"phone_number_id": PHONE_NUMBER_ID, "to": "213555000000", "text": "9500 DA"}


async def test_post_deduplicates_repeated_delivery(client, session, monkeypatch):
    await make_business(session, whatsapp_phone_number_id=PHONE_NUMBER_ID)

    async def fake_run_agent(session, history):
        return AgentReply(status="quote_ready", message="9500 DA", lines=[], confidence=95)

    async def fake_send_message(phone_number_id, to, text):
        pass

    monkeypatch.setattr("app.routers.webhooks.whatsapp.run_agent", fake_run_agent)
    monkeypatch.setattr("app.routers.webhooks.whatsapp.send_message", fake_send_message)

    body_bytes = json.dumps(_payload(message_id="wamid.dup")).encode()
    headers = {"X-Hub-Signature-256": _sign(body_bytes), "Content-Type": "application/json"}

    await client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)
    await client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)

    result = await session.execute(
        select(Message).where(Message.whatsapp_message_id == "wamid.dup")
    )
    assert len(result.scalars().all()) == 1


async def test_post_survives_concurrent_duplicate(client, session, monkeypatch):
    """Two overlapping deliveries can both pass message_exists before either commits —
    the second must lose gracefully to the DB's unique constraint, not 500."""
    await make_business(session, whatsapp_phone_number_id=PHONE_NUMBER_ID)

    async def fake_run_agent(session, history):
        return AgentReply(status="quote_ready", message="9500 DA", lines=[], confidence=95)

    async def fake_send_message(phone_number_id, to, text):
        pass

    async def always_false(session, whatsapp_message_id):
        return False

    monkeypatch.setattr("app.routers.webhooks.whatsapp.run_agent", fake_run_agent)
    monkeypatch.setattr("app.routers.webhooks.whatsapp.send_message", fake_send_message)
    monkeypatch.setattr("app.routers.webhooks.whatsapp.message_exists", always_false)

    body_bytes = json.dumps(_payload(message_id="wamid.race")).encode()
    headers = {"X-Hub-Signature-256": _sign(body_bytes), "Content-Type": "application/json"}

    first = await client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)
    second = await client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200  # not 500 — the race loser skips cleanly

    result = await session.execute(
        select(Message).where(Message.whatsapp_message_id == "wamid.race")
    )
    assert len(result.scalars().all()) == 1


async def test_post_passes_prior_history_to_agent(client, session, monkeypatch):
    business = await make_business(session, whatsapp_phone_number_id=PHONE_NUMBER_ID)
    wa_client = await get_or_create_client(session, business.id, "213555000000", name="Yacine")
    conversation = await get_or_create_conversation(
        session, business.id, wa_client.id, Channel.whatsapp
    )
    await save_message(session, conversation.id, Sender.client, "salut, prix des flyers?")
    await save_message(session, conversation.id, Sender.agent, "quelle quantité ?")
    await session.commit()

    seen_history = {}

    async def fake_run_agent(session, history):
        seen_history["value"] = history
        return AgentReply(status="quote_ready", message="9500 DA", lines=[], confidence=95)

    async def fake_send_message(phone_number_id, to, text):
        pass

    monkeypatch.setattr("app.routers.webhooks.whatsapp.run_agent", fake_run_agent)
    monkeypatch.setattr("app.routers.webhooks.whatsapp.send_message", fake_send_message)

    body_bytes = json.dumps(_payload(message_id="wamid.2", text="500 flyers")).encode()
    headers = {"X-Hub-Signature-256": _sign(body_bytes), "Content-Type": "application/json"}

    response = await client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)

    assert response.status_code == 200
    history = seen_history["value"]
    assert [c.parts[0].text for c in history] == [
        "salut, prix des flyers?",
        "quelle quantité ?",
        "500 flyers",
    ]
    assert [c.role for c in history] == ["user", "model", "user"]


async def test_post_unknown_phone_number_id_returns_200_without_saving(client, session):
    body_bytes = json.dumps(_payload()).encode()
    headers = {"X-Hub-Signature-256": _sign(body_bytes), "Content-Type": "application/json"}

    response = await client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)

    assert response.status_code == 200
    result = await session.execute(select(Message))
    assert result.scalars().all() == []


async def test_post_holds_low_confidence_reply(client, session, monkeypatch):
    await make_business(session, whatsapp_phone_number_id=PHONE_NUMBER_ID)

    async def fake_run_agent(session, history):
        return AgentReply(status="needs_info", message="ça va, et toi ?", lines=[], confidence=15)

    sent = {}

    async def fake_send_message(phone_number_id, to, text):
        sent["called"] = True

    monkeypatch.setattr("app.routers.webhooks.whatsapp.run_agent", fake_run_agent)
    monkeypatch.setattr("app.routers.webhooks.whatsapp.send_message", fake_send_message)

    body_bytes = json.dumps(_payload(text="ça va?")).encode()
    headers = {"X-Hub-Signature-256": _sign(body_bytes), "Content-Type": "application/json"}
    response = await client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)

    assert response.status_code == 200
    assert "called" not in sent

    result = await session.execute(select(Message).where(Message.sender == Sender.agent))
    assert result.scalars().all() == []

    result = await session.execute(select(Quote))
    quotes = result.scalars().all()
    assert len(quotes) == 1
    assert quotes[0].status == QuoteStatus.pending
    assert quotes[0].hold_reason == HoldReason.low_confidence
    assert quotes[0].draft_message == "ça va, et toi ?"


async def test_post_holds_rate_limited_reply_even_if_confident(client, session, monkeypatch):
    await make_business(session, whatsapp_phone_number_id=PHONE_NUMBER_ID)

    async def fake_run_agent(session, history):
        return AgentReply(status="quote_ready", message="9500 DA", lines=[], confidence=95)

    async def always_rate_limited(conversation_id):
        return True

    monkeypatch.setattr("app.routers.webhooks.whatsapp.run_agent", fake_run_agent)
    monkeypatch.setattr("app.routers.webhooks.whatsapp.is_rate_limited", always_rate_limited)

    body_bytes = json.dumps(_payload()).encode()
    headers = {"X-Hub-Signature-256": _sign(body_bytes), "Content-Type": "application/json"}
    response = await client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)

    assert response.status_code == 200

    result = await session.execute(select(Quote))
    quotes = result.scalars().all()
    assert len(quotes) == 1
    assert quotes[0].status == QuoteStatus.pending
    assert quotes[0].hold_reason == HoldReason.rate_limited


async def test_post_records_auto_sent_quote(client, session, monkeypatch):
    await make_business(session, whatsapp_phone_number_id=PHONE_NUMBER_ID)

    async def fake_run_agent(session, history):
        return AgentReply(status="quote_ready", message="9500 DA", lines=[], confidence=95)

    async def fake_send_message(phone_number_id, to, text):
        pass

    monkeypatch.setattr("app.routers.webhooks.whatsapp.run_agent", fake_run_agent)
    monkeypatch.setattr("app.routers.webhooks.whatsapp.send_message", fake_send_message)

    body_bytes = json.dumps(_payload()).encode()
    headers = {"X-Hub-Signature-256": _sign(body_bytes), "Content-Type": "application/json"}
    response = await client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)

    assert response.status_code == 200

    result = await session.execute(select(Quote))
    quotes = result.scalars().all()
    assert len(quotes) == 1
    assert quotes[0].status == QuoteStatus.auto_sent
    assert quotes[0].confidence == 95
