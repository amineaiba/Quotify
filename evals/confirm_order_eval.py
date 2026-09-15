# Run:  docker compose exec api python evals/confirm_order_eval.py  [-v]
#
# Costs a real Gemini call per case (the agent decides whether to call
# confirm_order) — run by hand, not in CI. Writes and cleans up its own
# fake business/conversation rows in the dev DB.

import argparse
import asyncio
import json
import logging
import uuid
from pathlib import Path

from google.genai import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_agent, user_message
from app.db.session import async_session_factory
from app.models.business import Business, Client
from app.models.conversation import Channel, Conversation
from app.models.order import Order
from app.models.quote import QuoteStatus
from app.schemas.pricing import PriceBreakdown
from app.services.quotes import save_quote

logger = logging.getLogger(__name__)

DATASET_PATH = Path(__file__).parent / "datasets" / "confirmations.json"
CASES = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

_QUOTE_TEXT = "500 flyers A5 recto-verso : 9500 DA."
_LINE = PriceBreakdown(
    item_id=uuid.uuid4(), name="Flyer A5 quadri recto-verso", unit="flyer",
    quantity=500, unit_price=19, applied_min_qty=500, total=9500,
)


def _model_message(text: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=text)])


async def _make_conversation_with_quote(session: AsyncSession) -> Conversation:
    business = Business(
        name="Eval Business",
        email=f"eval-{uuid.uuid4()}@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    client = Client(phone_number=f"+213555{uuid.uuid4().int % 1_000_000:06d}", name="Eval Client")
    business.clients.append(client)
    session.add(business)
    await session.flush()

    conversation = Conversation(
        business_id=business.id, client_id=client.id, channel=Channel.whatsapp
    )
    session.add(conversation)
    await session.commit()

    await save_quote(session, conversation.id, _QUOTE_TEXT, 95, [_LINE], QuoteStatus.auto_sent)
    return conversation


async def _order_exists(session: AsyncSession, conversation_id: uuid.UUID) -> bool:
    result = await session.execute(select(Order).where(Order.conversation_id == conversation_id))
    return result.scalar_one_or_none() is not None


async def run_case(session: AsyncSession, case: dict) -> bool:
    conversation = await _make_conversation_with_quote(session)
    business_id = conversation.business_id
    try:
        history = [
            user_message("500 flyers A5 recto verso, chhal?"),
            _model_message(_QUOTE_TEXT),
            user_message(case["confirm_text"]),
        ]
        await run_agent(session, history, conversation_id=conversation.id)
        return await _order_exists(session, conversation.id) == case["should_confirm"]
    finally:
        business = await session.get(Business, business_id)
        await session.delete(business)
        await session.commit()


async def main(verbose: bool) -> None:
    correct = 0
    async with async_session_factory() as session:
        for case in CASES:
            ok = await run_case(session, case)
            correct += 1 if ok else 0
            mark = "HIT " if ok else "MISS"
            logger.debug(
                "%s should_confirm=%-5s  %s", mark, case["should_confirm"], case["confirm_text"]
            )
    logger.info(
        "confirm_order accuracy = %.2f   (%d/%d)", correct / len(CASES), correct, len(CASES)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="show per-case hit/miss")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")
    asyncio.run(main(args.verbose))
