from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import messages_to_history, run_agent, user_message
from app.core.exceptions import AgentTurnLimitExceeded
from app.db.session import get_session
from app.models.conversation import Sender
from app.schemas.agent import AgentReply, AgentRequest
from app.services.conversation import get_conversation_by_id, get_conversation_history, save_message

router = APIRouter()


@router.post("/messages", response_model=AgentReply)
async def messages(
    body: AgentRequest,
    session: AsyncSession = Depends(get_session),
) -> AgentReply:
    conversation = None
    if body.conversation_id is None:
        history = [user_message(body.message)]
    else:
        conversation = await get_conversation_by_id(session, body.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="conversation not found")
        await save_message(session, conversation.id, Sender.client, body.message)
        history = messages_to_history(await get_conversation_history(session, conversation.id))

    try:
        reply = await run_agent(session, history)
    except AgentTurnLimitExceeded as err:
        raise HTTPException(status_code=503, detail="agent did not finish") from err

    if conversation is not None:
        await save_message(session, conversation.id, Sender.agent, reply.message)

    return reply
