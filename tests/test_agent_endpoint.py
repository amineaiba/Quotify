from app.agent.loop import MAX_TURNS
from tests.conftest import FakeCall, FakeClient, FakeResponse, seed_flyer


async def test_messages_prices_item_and_returns_quote_ready(client, session, monkeypatch):
    await seed_flyer(session)
    responses = [
        FakeResponse(
            function_calls=[FakeCall(name="calc_price", args={"item_id": 1, "quantity": 500})]
        ),
        FakeResponse(function_calls=[], text="500 flyers A5 recto-verso : 9500 DA."),
    ]
    client_double = FakeClient(responses)
    monkeypatch.setattr("app.agent.loop.get_client", lambda: client_double)

    response = await client.post(
        "/api/v1/agent/messages", json={"message": "500 flyers A5 recto verso, chhal?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "quote_ready"
    assert body["lines"][0]["total"] == 9500


async def test_messages_no_tool_calls_returns_needs_info(client, session, monkeypatch):
    responses = [FakeResponse(function_calls=[], text="Quelle quantité voulez-vous ?")]
    client_double = FakeClient(responses)
    monkeypatch.setattr("app.agent.loop.get_client", lambda: client_double)

    response = await client.post("/api/v1/agent/messages", json={"message": "svp le prix"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_info"
    assert body["lines"] == []


async def test_messages_rejects_empty_message(client, session):
    response = await client.post("/api/v1/agent/messages", json={"message": ""})

    assert response.status_code == 422


async def test_messages_turn_limit_returns_503(client, session, monkeypatch):
    await seed_flyer(session)
    always_calls = FakeResponse(
        function_calls=[FakeCall(name="calc_price", args={"item_id": 1, "quantity": 500})]
    )
    responses = [always_calls] * MAX_TURNS
    client_double = FakeClient(responses)
    monkeypatch.setattr("app.agent.loop.get_client", lambda: client_double)

    response = await client.post("/api/v1/agent/messages", json={"message": "500 flyers"})

    assert response.status_code == 503
