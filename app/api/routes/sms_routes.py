import logging

from fastapi import APIRouter, Depends, Form
from fastapi.responses import Response

from app.api.deps import get_sms_workflow
from app.domain.workflows.sms_workflow import SMSWorkflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sms", tags=["sms"])


@router.post("/incoming")
async def incoming_sms(
    From: str = Form(...),
    Body: str = Form(...),
    workflow: SMSWorkflow = Depends(get_sms_workflow),
):
    """Twilio webhook for incoming SMS messages. Returns TwiML response."""
    response_text = await workflow.handle_incoming_sms(from_number=From, body=Body)

    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{response_text}</Message></Response>"
    )
    return Response(content=twiml, media_type="application/xml")
