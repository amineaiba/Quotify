from google.genai import types

from app.agent.graph import AgentState, call_model, run_tools
from tests.conftest import (
    FLYER_ID,
    GraphFakeClient,
    graph_text_content,
    graph_tool_call_content,
    seed_flyer,
)

# --- call_model ------------------------------------------------------------


async def test_call_model_appends_response_to_history(monkeypatch):
    monkeypatch.setattr(
        "app.agent.graph.get_client",
        lambda: GraphFakeClient([graph_text_content("bonjour")]),
    )
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
