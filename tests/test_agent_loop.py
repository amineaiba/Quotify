from dataclasses import dataclass, field

import pytest
from pydantic import ValidationError

from app.agent.loop import MAX_TURNS, run_agent
from app.core.exceptions import AgentTurnLimitExceeded
from app.llm.embeddings import EMBED_DIM
from app.models.catalog import CatalogItem, CatalogItemTier
from app.schemas.agent import AgentReply


def test_agent_reply_defaults_to_empty_lines():
    reply = AgentReply(status="needs_info", message="what quantity?")
    assert reply.lines == []


def test_agent_reply_rejects_unknown_status():
    with pytest.raises(ValidationError):
        AgentReply(status="something_else", message="hi")


# --- test doubles for the Gemini client -------------------------------
# run_agent only ever touches response.candidates[0].content,
# response.function_calls, and response.text — these fakes provide
# exactly that, nothing more.


@dataclass
class FakeCall:
    name: str
    args: dict


@dataclass
class FakeCandidate:
    content: object = None


@dataclass
class FakeResponse:
    function_calls: list
    text: str = ""
    candidates: list = field(default_factory=lambda: [FakeCandidate()])


class FakeModels:
    def __init__(self, responses):
        self._responses = iter(responses)

    def generate_content(self, **kwargs):
        return next(self._responses)


class FakeClient:
    def __init__(self, responses):
        self.models = FakeModels(responses)


async def _seed_flyer(session):
    session.add(
        CatalogItem(
            id=1,
            name="Flyer A5 quadri recto-verso",
            unit="flyer",
            tiers=[
                CatalogItemTier(min_qty=100, unit_price=30),
                CatalogItemTier(min_qty=500, unit_price=19),
            ],
            embedding=[0.0] * EMBED_DIM,
        )
    )
    await session.commit()


# --- run_agent tests -----------------------------------------------------


async def test_run_agent_prices_item_and_returns_quote_ready(session, monkeypatch):
    await _seed_flyer(session)
    responses = [
        FakeResponse(
            function_calls=[FakeCall(name="calc_price", args={"item_id": 1, "quantity": 500})]
        ),
        FakeResponse(function_calls=[], text="500 flyers A5 recto-verso : 9500 DA."),
    ]
    client = FakeClient(responses)
    monkeypatch.setattr("app.agent.loop.get_client", lambda: client)

    reply = await run_agent(session, "500 flyers A5 recto verso, chhal?")

    assert reply.status == "quote_ready"
    assert reply.lines[0].total == 9500
    assert reply.message == "500 flyers A5 recto-verso : 9500 DA."


async def test_run_agent_no_tool_calls_returns_needs_info(session, monkeypatch):
    responses = [FakeResponse(function_calls=[], text="Quelle quantité voulez-vous ?")]
    client = FakeClient(responses)
    monkeypatch.setattr("app.agent.loop.get_client", lambda: client)

    reply = await run_agent(session, "svp le prix des flyers")

    assert reply.status == "needs_info"
    assert reply.lines == []
    assert reply.message == "Quelle quantité voulez-vous ?"


async def test_run_agent_below_minimum_continues_without_crashing(session, monkeypatch):
    await _seed_flyer(session)
    responses = [
        FakeResponse(
            function_calls=[FakeCall(name="calc_price", args={"item_id": 1, "quantity": 50})]
        ),
        FakeResponse(function_calls=[], text="Le minimum pour cet article est 100."),
    ]
    client = FakeClient(responses)
    monkeypatch.setattr("app.agent.loop.get_client", lambda: client)

    reply = await run_agent(session, "50 flyers A5 recto verso")

    assert reply.status == "needs_info"
    assert reply.lines == []
    assert reply.message == "Le minimum pour cet article est 100."


async def test_run_agent_raises_after_max_turns(session, monkeypatch):
    await _seed_flyer(session)
    always_calls = FakeResponse(
        function_calls=[FakeCall(name="calc_price", args={"item_id": 1, "quantity": 500})]
    )
    responses = [always_calls] * MAX_TURNS
    client = FakeClient(responses)
    monkeypatch.setattr("app.agent.loop.get_client", lambda: client)

    with pytest.raises(AgentTurnLimitExceeded):
        await run_agent(session, "500 flyers")
