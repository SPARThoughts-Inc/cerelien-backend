from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Conversation(BaseModel):
    id: int
    patient_id: int
    channel: Literal["sms", "voice", "web"]
    status: str = "active"
    started_at: datetime | None = None
    ended_at: datetime | None = None
