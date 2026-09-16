# Run:  docker compose exec api python evals/multi_item_eval.py  [-v]
#
# Costs real Gemini calls (embeddings for the seeded catalog, then the agent
# turns for each case) — run by hand, not in CI. Seeds its own throwaway
# business + catalog, cleans both up after the run.

import argparse
import asyncio
import json
import logging
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_agent, user_message
from app.db.session import async_session_factory
from app.llm.embeddings import embed
from app.models.business import Business, Client
from app.models.catalog import CatalogItem, CatalogItemTier
from app.models.conversation import Channel, Conversation

logger = logging.getLogger(__name__)

DATASET_PATH = Path(__file__).parent / "datasets" / "multi_item.json"
CASES = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

CATALOG = [
    {"name": "Flyer A5 quadri recto-verso", "unit": "flyer", "tiers": [(100, 30), (500, 19)]},
    {"name": "Carte de visite quadri", "unit": "carte", "tiers": [(100, 15), (500, 10)]},
    {"name": "Banderole grand format", "unit": "banderole", "tiers": [(1, 2000)]},
]


async def _seed_business_and_catalog(session: AsyncSession) -> Business:
    business = Business(
        name="Eval Print Shop",
        email=f"eval-multi-{uuid.uuid4()}@example.com",
        hashed_password="hashed",
        is_active=True,
        is_verified=False,
        is_superuser=False,
    )
    session.add(business)
    await session.flush()

    for item in CATALOG:
        [vector] = embed([item["name"]], "RETRIEVAL_DOCUMENT")
        session.add(
            CatalogItem(
                business_id=business.id,
                name=item["name"],
                unit=item["unit"],
                embedding=vector,
                tiers=[CatalogItemTier(min_qty=q, unit_price=p) for q, p in item["tiers"]],
            )
        )
    await session.commit()
    return business


async def _make_conversation(session: AsyncSession, business: Business) -> Conversation:
    client = Client(
        business_id=business.id,
        phone_number=f"+213555{uuid.uuid4().int % 1_000_000:06d}",
        name="Eval Client",
    )
    session.add(client)
    await session.flush()

    conversation = Conversation(
        business_id=business.id, client_id=client.id, channel=Channel.whatsapp
    )
    session.add(conversation)
    await session.commit()
    return conversation


async def run_case(session: AsyncSession, business: Business, case: dict) -> bool:
    conversation = await _make_conversation(session, business)
    reply = await run_agent(
        session,
        [user_message(case["text"])],
        conversation_id=conversation.id,
        business_id=business.id,
    )
    got = sorted(line.name for line in reply.lines)
    want = sorted(case["expected_items"])
    return got == want


async def main(verbose: bool) -> None:
    correct = 0
    async with async_session_factory() as session:
        business = await _seed_business_and_catalog(session)
        try:
            for i, case in enumerate(CASES):
                if i > 0:
                    # stays under Gemini's free-tier rate limit (15 requests/min) —
                    # each case makes 2+ real calls.
                    await asyncio.sleep(10)
                logger.info("--- case %d/%d: %r ---", i + 1, len(CASES), case["text"])
                ok = await run_case(session, business, case)
                correct += 1 if ok else 0
                mark = "HIT " if ok else "MISS"
                logger.info("%s expected=%s  %s", mark, case["expected_items"], case["text"])
        finally:
            business = await session.get(Business, business.id)
            await session.delete(business)
            await session.commit()
    logger.info(
        "multi_item accuracy = %.2f   (%d/%d)", correct / len(CASES), correct, len(CASES)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="also show each tool call the agent makes"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(name)-16s %(message)s",
    )
    for noisy in ("httpx", "httpcore", "langgraph", "google_genai", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    asyncio.run(main(args.verbose))
