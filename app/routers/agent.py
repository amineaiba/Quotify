from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.loop import run_agent
from app.core.exceptions import AgentTurnLimitExceeded
from app.db.session import get_session
from app.schemas.agent import AgentReply, AgentRequest

router = APIRouter()


@router.post("/messages", response_model=AgentReply)
async def messages(
    body: AgentRequest,
    session: AsyncSession = Depends(get_session),
) -> AgentReply:
    try:
        return await run_agent(session, body.message)
    except AgentTurnLimitExceeded as err:
        raise HTTPException(status_code=503, detail="agent did not finish") from err
