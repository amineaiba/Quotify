import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.conversation import Channel
from app.models.order import OrderStatus
from app.schemas.conversation import ClientOut, QuoteSummary


class OrderSummary(BaseModel):
    id: uuid.UUID
    created_at: datetime
    status: OrderStatus
    client: ClientOut
    channel: Channel
    quote: QuoteSummary


class OrderDetail(OrderSummary):
    conversation_id: uuid.UUID
