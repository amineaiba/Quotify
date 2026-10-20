import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.pricing import PriceBreakdown


class AgentRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: uuid.UUID | None = None


class AgentReply(BaseModel):
    status: Literal["needs_info", "quote_ready"]
    message: str
    lines: list[PriceBreakdown] = []
    confidence: int | None = None
