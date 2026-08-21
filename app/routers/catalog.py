from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.catalog import CatalogItemOut, SearchRequest
from app.services.catalog import search_catalog

router = APIRouter()


@router.post("/search", response_model=list[CatalogItemOut])
async def search(
    body: SearchRequest,
    session: AsyncSession = Depends(get_session),
) -> list[CatalogItemOut]:
    items = await search_catalog(session, body.message, body.k)
    return [CatalogItemOut.model_validate(item) for item in items]
