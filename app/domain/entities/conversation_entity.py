from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Conversation(BaseModel):
    id: UUID
    patient_id: UUID
    channel: Literal["web_chat", "voice", "sms"]
    started_at: datetime | None = None
    ended_at: datetime | None = None
