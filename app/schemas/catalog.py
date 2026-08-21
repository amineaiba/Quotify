from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    message: str = Field(min_length=1, description="the raw client message")
    k: int = Field(default=3, ge=1, le=20)


class CatalogItemOut(BaseModel):
    id: int
    name: str
    unit: str

    model_config = {"from_attributes": True}
