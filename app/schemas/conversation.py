import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.conversation import Channel, Sender
from app.models.quote import QuoteStatus
from app.schemas.pricing import PriceBreakdown

ConversationStatus = Literal["attention", "held", "auto_sent"]


class ClientOut(BaseModel):
    name: str | None
    phone_number: str

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: uuid.UUID
    sender: Sender
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LastMessageOut(BaseModel):
    content: str
    sender: Sender
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: uuid.UUID
    channel: Channel
    client: ClientOut
    last_message: LastMessageOut | None
    status: ConversationStatus
    total: int | None


class QuoteSummary(BaseModel):
    status: QuoteStatus
    lines: list[PriceBreakdown]
    subtotal: int


class ConversationDetail(BaseModel):
    id: uuid.UUID
    channel: Channel
    client: ClientOut
    messages: list[MessageOut]
    latest_quote: QuoteSummary | None
