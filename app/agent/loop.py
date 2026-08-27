import logging

from google.genai import types
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


async def run_agent(session: AsyncSession, message: str) -> AgentReply:
    history = [types.Content(role="user", parts=[types.Part(text=message)])]
    lines: list[PriceBreakdown] = []

    for turn in range(MAX_TURNS):
        response = get_client().models.generate_content(
            model=get_settings().agent_model,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[TOOLS],
            ),
        )
        history.append(response.candidates[0].content)

        if not response.function_calls:
            status = "quote_ready" if lines else "needs_info"
            logger.debug("turn %d: no function calls, done (%s)", turn, status)
            return AgentReply(status=status, message=response.text, lines=lines)

        for call in response.function_calls:
            logger.debug("turn %d: calling %s(%s)", turn, call.name, call.args)
            result = await dispatch(session, call.name, call.args)
            logger.debug("turn %d: %s returned %s", turn, call.name, result)
            if call.name == "calc_price" and "error" not in result:
                lines.append(PriceBreakdown(**result))
            history.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=call.name, response=result
                            )
                        )
                    ],
                )
            )

    raise AgentTurnLimitExceeded()
