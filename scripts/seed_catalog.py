# Run:  docker compose exec api python scripts/seed_catalog.py

import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select

from app.db.session import async_session_factory
from app.llm.embeddings import embed
from app.models.catalog import CatalogItem, CatalogItemTier

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog.json"


async def seed() -> None:
    items = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    async with async_session_factory() as session:
        existing_names = set((await session.execute(select(CatalogItem.name))).scalars().all())
        to_insert = [item for item in items if item["name"] not in existing_names]

        logger.info(
            "%d items in catalog.json, %d already seeded", len(items), len(items) - len(to_insert)
        )
        if not to_insert:
            logger.info("nothing to do")
            return

        vectors = embed([item["name"] for item in to_insert], "RETRIEVAL_DOCUMENT")

        session.add_all(
            CatalogItem(
                name=item["name"],
                unit=item["unit"],
                tiers=[CatalogItemTier(**t) for t in item["tiers"]],
                embedding=vector,
            )
            for item, vector in zip(to_insert, vectors, strict=True)
        )
        await session.commit()
        logger.info("inserted %d rows", len(to_insert))


if __name__ == "__main__":
    asyncio.run(seed())
