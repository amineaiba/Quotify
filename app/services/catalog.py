from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.embeddings import embed
from app.models.catalog import CatalogItem


async def search_catalog(session: AsyncSession, message: str, k: int) -> list[CatalogItem]:
    """Top k catalog items closest in meaning to `message`, best match first."""
    [query_vector] = embed([message], "RETRIEVAL_QUERY")

    # cosine_distance: smaller = closer. DESC here would return the worst matches.
    stmt = (
        select(CatalogItem)
        .order_by(CatalogItem.embedding.cosine_distance(query_vector))
        .limit(k)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
