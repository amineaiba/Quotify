import logging
import operator
from typing import Annotated, TypedDict

from google.genai import types
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.prompts.system import SYSTEM_PROMPT
from app.agent.tools import TOOLS, dispatch
from app.core.config import get_settings
from app.core.exceptions import AgentTurnLimitExceeded
from app.llm.client import get_client
from app.schemas.agent import AgentReply
from app.schemas.pricing import PriceBreakdown

logger = logging.getLogger(__name__)

MAX_TURNS = 8


class AgentState(TypedDict):
    history: Annotated[list[types.Content], operator.add]
    lines: Annotated[list[PriceBreakdown], operator.add]


def _function_calls(content: types.Content) -> list[types.FunctionCall]:
    return [part.function_call for part in content.parts if part.function_call]


async def call_model(state: AgentState, config: RunnableConfig) -> dict:
    response = get_client().models.generate_content(
        model=get_settings().agent_model,
        contents=state["history"],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[TOOLS],
        ),
    )
    return {"history": [response.candidates[0].content]}


async def run_tools(state: AgentState, config: RunnableConfig) -> dict:
    session: AsyncSession = config["configurable"]["session"]
    last_message = state["history"][-1]
    new_history: list[types.Content] = []
    new_lines: list[PriceBreakdown] = []

    for call in _function_calls(last_message):
        logger.debug("calling %s(%s)", call.name, call.args)
        result = await dispatch(session, call.name, call.args)
        logger.debug("%s returned %s", call.name, result)
        if call.name == "calc_price" and "error" not in result:
            new_lines.append(PriceBreakdown(**result))
        new_history.append(
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        function_response=types.FunctionResponse(name=call.name, response=result)
                    )
                ],
            )
        )

    return {"history": new_history, "lines": new_lines}


def has_tool_calls(state: AgentState) -> str:
    last_message = state["history"][-1]
    return "run_tools" if _function_calls(last_message) else END


graph = StateGraph(AgentState)
graph.add_node("call_model", call_model)
graph.add_node("run_tools", run_tools)
graph.set_entry_point("call_model")
graph.add_conditional_edges("call_model", has_tool_calls)
graph.add_edge("run_tools", "call_model")
COMPILED_GRAPH = graph.compile()


async def run_agent(session: AsyncSession, message: str) -> AgentReply:
    initial_state: AgentState = {
        "history": [types.Content(role="user", parts=[types.Part(text=message)])],
        "lines": [],
    }
    config = {
        "configurable": {"session": session},
        "recursion_limit": MAX_TURNS * 2,
    }
    try:
        final_state = await COMPILED_GRAPH.ainvoke(initial_state, config=config)
    except GraphRecursionError as err:
        raise AgentTurnLimitExceeded() from err

    lines = final_state["lines"]
    status = "quote_ready" if lines else "needs_info"
    message_text = final_state["history"][-1].parts[0].text
    return AgentReply(status=status, message=message_text, lines=lines)
