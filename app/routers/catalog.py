import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.users import current_active_business
from app.db.session import get_session
from app.models.business import Business
from app.schemas.catalog import CatalogItemDetail, CatalogItemOut, CatalogItemWrite, SearchRequest
from app.services.catalog import (
    create_item,
    delete_item,
    get_item,
    list_items,
    search_catalog,
    update_item,
)

router = APIRouter()


@router.post("/search", response_model=list[CatalogItemOut])
async def search(
    body: SearchRequest,
    session: AsyncSession = Depends(get_session),
) -> list[CatalogItemOut]:
    items = await search_catalog(session, body.message, body.k)
    return [CatalogItemOut.model_validate(item) for item in items]


@router.get("/items", response_model=list[CatalogItemDetail])
async def list_catalog_items(
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> list[CatalogItemDetail]:
    items = await list_items(session, business.id)
    return [CatalogItemDetail.model_validate(item) for item in items]


@router.get("/items/{item_id}", response_model=CatalogItemDetail)
async def get_catalog_item(
    item_id: uuid.UUID,
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> CatalogItemDetail:
    item = await get_item(session, business.id, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return CatalogItemDetail.model_validate(item)


@router.post("/items", response_model=CatalogItemDetail, status_code=status.HTTP_201_CREATED)
async def create_catalog_item(
    body: CatalogItemWrite,
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> CatalogItemDetail:
    item = await create_item(session, business.id, body)
    return CatalogItemDetail.model_validate(item)


@router.put("/items/{item_id}", response_model=CatalogItemDetail)
async def update_catalog_item(
    item_id: uuid.UUID,
    body: CatalogItemWrite,
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> CatalogItemDetail:
    item = await update_item(session, business.id, item_id, body)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return CatalogItemDetail.model_validate(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_catalog_item(
    item_id: uuid.UUID,
    business: Business = Depends(current_active_business),
    session: AsyncSession = Depends(get_session),
) -> None:
    deleted = await delete_item(session, business.id, item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
