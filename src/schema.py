from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SMSRequest(BaseModel):
    recipient: str = Field(
        ..., description="Recipient's phone number", pattern=r"^\+?[1-9]\d{1,14}$"
    )
    message: str = Field(..., description="Message to send")


class SMSResponse(BaseModel):
    success: bool
    message_id: str
    provider: str
    timestamp: datetime
    error: Optional[str] = None
