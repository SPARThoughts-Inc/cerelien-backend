from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: UUID | None = None


class ChatStartResponse(BaseModel):
    conversation_id: UUID
