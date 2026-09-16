import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.quote import HoldReason, QuoteStatus
from app.schemas.conversation import ClientOut
from app.schemas.pricing import PriceBreakdown


class QuoteListItem(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    client: ClientOut
    draft_message: str
    confidence: int | None
    status: QuoteStatus
    hold_reason: HoldReason | None
    lines: list[PriceBreakdown]
    subtotal: int | None
    created_at: datetime


class QuoteApproveRequest(BaseModel):
    message: str


class QuoteActionResponse(BaseModel):
    id: uuid.UUID
    status: QuoteStatus
    final_message: str | None
    reviewed_at: datetime
