import uuid

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    message: str = Field(min_length=1, description="the raw client message")
    k: int = Field(default=3, ge=1, le=20)


class CatalogItemOut(BaseModel):
    id: uuid.UUID
    name: str
    unit: str

    model_config = {"from_attributes": True}


class CatalogItemTierIn(BaseModel):
    min_qty: int = Field(gt=0)
    unit_price: int = Field(gt=0)


class CatalogItemTierOut(BaseModel):
    id: uuid.UUID
    min_qty: int
    unit_price: int

    model_config = {"from_attributes": True}


class CatalogItemWrite(BaseModel):
    name: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    tiers: list[CatalogItemTierIn] = Field(min_length=1)

    @field_validator("tiers")
    @classmethod
    def unique_min_qty(cls, tiers: list[CatalogItemTierIn]) -> list[CatalogItemTierIn]:
        seen = [t.min_qty for t in tiers]
        if len(seen) != len(set(seen)):
            raise ValueError("tiers must have unique min_qty values")
        return tiers


class CatalogItemDetail(CatalogItemOut):
    tiers: list[CatalogItemTierOut]
