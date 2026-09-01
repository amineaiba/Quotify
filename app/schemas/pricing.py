import uuid

from pydantic import BaseModel


class PriceBreakdown(BaseModel):
    item_id: uuid.UUID
    name: str
    unit: str
    quantity: int
    unit_price: int
    applied_min_qty: int
    total: int
