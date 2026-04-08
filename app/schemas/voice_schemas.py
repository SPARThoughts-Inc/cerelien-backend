from pydantic import BaseModel


class OutboundCallRequest(BaseModel):
    patient_id: int
    reason: str


class OutboundCallResponse(BaseModel):
    success: bool
    call_sid: str | None = None
    message: str | None = None


class VoiceTokenResponse(BaseModel):
    token: str
