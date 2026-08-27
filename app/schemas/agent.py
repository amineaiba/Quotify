from typing import Literal

from pydantic import BaseModel

from app.schemas.pricing import PriceBreakdown


class AgentReply(BaseModel):
    status: Literal["needs_info", "quote_ready"]
    message: str
    lines: list[PriceBreakdown] = []
