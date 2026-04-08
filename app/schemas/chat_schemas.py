from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatStartResponse(BaseModel):
    conversation_id: int
