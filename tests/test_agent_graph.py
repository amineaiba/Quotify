import pytest
from google.genai import types

from app.agent.graph import MAX_TURNS, AgentState, call_model, run_agent, run_tools
from app.core.exceptions import AgentTurnLimitExceeded
from tests.conftest import (
    FLYER_ID,
    GraphFakeClient,
    graph_text_content,
    graph_tool_call_content,
    seed_flyer,
)

# --- call_model ------------------------------------------------------------


async def test_call_model_appends_response_to_history(monkeypatch):
    client_double = GraphFakeClient([graph_text_content("bonjour")])
    monkeypatch.setattr("app.agent.graph.get_client", lambda: client_double)
    state: AgentState = {
        "history": [types.Content(role="user", parts=[types.Part(text="salut")])],
        "lines": [],
    }

    result = await call_model(state, config={})

    assert result["history"] == [graph_text_content("bonjour")]


# --- run_tools ---------------------------------------------------------


async def test_run_tools_dispatches_calc_price_and_records_line(session):
    await seed_flyer(session)
    state: AgentState = {
        "history": [
            graph_tool_call_content("calc_price", {"item_id": str(FLYER_ID), "quantity": 500})
        ],
        "lines": [],
    }
    config = {"configurable": {"session": session}}

    result = await run_tools(state, config)

    assert result["lines"][0].total == 9500
    assert len(result["history"]) == 1
    response_part = result["history"][0].parts[0].function_response
    assert response_part.name == "calc_price"


async def test_run_tools_below_minimum_returns_error_no_line(session):
    await seed_flyer(session)
    state: AgentState = {
        "history": [
            graph_tool_call_content("calc_price", {"item_id": str(FLYER_ID), "quantity": 50})
        ],
        "lines": [],
    }
    config = {"configurable": {"session": session}}

    result = await run_tools(state, config)

    assert result["lines"] == []
    response_part = result["history"][0].parts[0].function_response
    assert "error" in response_part.response


# --- run_agent -----------------------------------------------------------


async def test_run_agent_prices_item_and_returns_quote_ready(session, monkeypatch):
    await seed_flyer(session)
    responses = [
        graph_tool_call_content("calc_price", {"item_id": str(FLYER_ID), "quantity": 500}),
        graph_text_content("500 flyers A5 recto-verso : 9500 DA."),
    ]
    client_double = GraphFakeClient(responses)
    monkeypatch.setattr("app.agent.graph.get_client", lambda: client_double)

    reply = await run_agent(session, "500 flyers A5 recto verso, chhal?")

    assert reply.status == "quote_ready"
    assert reply.lines[0].total == 9500
    assert reply.message == "500 flyers A5 recto-verso : 9500 DA."


async def test_run_agent_no_tool_calls_returns_needs_info(session, monkeypatch):
    responses = [graph_text_content("Quelle quantité voulez-vous ?")]
    client_double = GraphFakeClient(responses)
    monkeypatch.setattr("app.agent.graph.get_client", lambda: client_double)

    reply = await run_agent(session, "svp le prix des flyers")

    assert reply.status == "needs_info"
    assert reply.lines == []
    assert reply.message == "Quelle quantité voulez-vous ?"


async def test_run_agent_below_minimum_continues_without_crashing(session, monkeypatch):
    await seed_flyer(session)
    responses = [
        graph_tool_call_content("calc_price", {"item_id": str(FLYER_ID), "quantity": 50}),
        graph_text_content("Le minimum pour cet article est 100."),
    ]
    client_double = GraphFakeClient(responses)
    monkeypatch.setattr("app.agent.graph.get_client", lambda: client_double)

    reply = await run_agent(session, "50 flyers A5 recto verso")

    assert reply.status == "needs_info"
    assert reply.lines == []
    assert reply.message == "Le minimum pour cet article est 100."


async def test_run_agent_raises_after_max_turns(session, monkeypatch):
    await seed_flyer(session)
    always_calls = graph_tool_call_content(
        "calc_price", {"item_id": str(FLYER_ID), "quantity": 500}
    )
    responses = [always_calls] * MAX_TURNS
    client_double = GraphFakeClient(responses)
    monkeypatch.setattr("app.agent.graph.get_client", lambda: client_double)

    with pytest.raises(AgentTurnLimitExceeded):
        await run_agent(session, "500 flyers")
