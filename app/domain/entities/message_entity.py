from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Message(BaseModel):
    id: UUID
    conversation_id: UUID
    role: Literal["user", "assistant", "system"]
    agent_name: str | None = None
    content: str
    created_at: datetime | None = None
