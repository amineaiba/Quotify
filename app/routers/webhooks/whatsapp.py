import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.graph import messages_to_history, run_agent
from app.core.config import get_settings
from app.core.rate_limit import is_rate_limited
from app.db.session import get_session, get_session_factory
from app.meta.signature import verify_signature
from app.models.conversation import Channel, Sender
from app.models.quote import HoldReason, QuoteStatus
from app.services.conversation import (
    get_business_by_whatsapp_phone_number_id,
    get_conversation_history,
    get_or_create_client,
    get_or_create_conversation,
    message_exists,
    save_message,
)
from app.services.quotes import save_quote
from app.whatsapp.client import send_message
from app.whatsapp.schemas import WebhookPayload, extract_text_messages

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    """One-time handshake Meta does when the webhook URL is registered."""
    settings = get_settings()
    if hub_verify_token != settings.meta_verify_token:
        raise HTTPException(status_code=403, detail="verify token mismatch")
    return Response(content=hub_challenge, media_type="text/plain")


@router.post("")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> dict:
    settings = get_settings()
    raw_body = await request.body()
    header_sig = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(raw_body, header_sig, settings.meta_app_secret):
        raise HTTPException(status_code=401, detail="bad signature")

    payload = WebhookPayload.model_validate_json(raw_body)
    inbound_messages = extract_text_messages(payload)

    for inbound in inbound_messages:
        business = await get_business_by_whatsapp_phone_number_id(session, inbound.phone_number_id)
        if business is None:
            logger.warning("no business for whatsapp_phone_number_id=%s", inbound.phone_number_id)
            continue

        if await message_exists(session, inbound.whatsapp_message_id):
            continue

        try:
            client = await get_or_create_client(
                session, business.id, inbound.from_number, name=inbound.contact_name
            )
            conversation = await get_or_create_conversation(
                session, business.id, client.id, Channel.whatsapp
            )
            await save_message(
                session,
                conversation.id,
                Sender.client,
                inbound.text,
                whatsapp_message_id=inbound.whatsapp_message_id,
            )
        except IntegrityError:
            # Meta sent overlapping retries of the same message — the
            # message_exists check above can't catch a race between two
            # concurrent deliveries. Whichever one lost the race just skips;
            # the winner already saved it and scheduled the reply.
            await session.rollback()
            continue

        background_tasks.add_task(
            _reply_to_message,
            conversation_id=conversation.id,
            phone_number_id=inbound.phone_number_id,
            to_number=inbound.from_number,
            session_factory=session_factory,
        )

    return {"status": "ok"}


async def _reply_to_message(
    conversation_id,
    phone_number_id: str,
    to_number: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Runs after the HTTP response is sent — opens its own DB session,
    since the request's session is closed by then. Any failure here is
    logged, never re-raised: no retry this phase (see Hardening in the
    roadmap), but a crash here must not take down the process.
    """
    try:
        async with session_factory() as session:
            history = messages_to_history(await get_conversation_history(session, conversation_id))
            reply = await run_agent(session, history)

            hold_reason: HoldReason | None = None
            if await is_rate_limited(conversation_id):
                hold_reason = HoldReason.rate_limited
            elif reply.confidence is None or reply.confidence < get_settings().confidence_threshold:
                hold_reason = HoldReason.low_confidence

            status = QuoteStatus.pending if hold_reason else QuoteStatus.auto_sent
            await save_quote(
                session,
                conversation_id,
                reply.message,
                reply.confidence,
                reply.lines,
                status,
                hold_reason,
            )

            if status == QuoteStatus.auto_sent:
                await save_message(session, conversation_id, Sender.agent, reply.message)
                await send_message(phone_number_id, to_number, reply.message)
    except Exception:
        logger.exception("failed to reply to conversation_id=%s", conversation_id)
