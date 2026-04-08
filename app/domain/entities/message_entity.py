from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Message(BaseModel):
    id: int
    conversation_id: int
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime | None = None
