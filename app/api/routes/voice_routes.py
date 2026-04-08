import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from app.api.deps import get_patient_workflow, get_twilio_adapter
from app.domain.workflows.patient_workflow import PatientWorkflow
from app.infrastructure.adapters.openai_realtime_adapter import OpenAIRealtimeAdapter
from app.infrastructure.adapters.twilio_adapter import TwilioAdapter
from app.schemas.voice_schemas import OutboundCallRequest, OutboundCallResponse, VoiceTokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

SYSTEM_INSTRUCTIONS = """You are a helpful diabetes consultation assistant for Cerelien.
Be warm, empathetic, and concise in your responses.
If the patient describes emergency symptoms (severe hypoglycemia, DKA, chest pain), advise calling 911 immediately.
Keep responses conversational and natural for voice interaction."""


@router.post("/incoming")
async def incoming_call():
    """Handle incoming Twilio voice call. Returns TwiML."""
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Say>Welcome to Cerelien, your diabetes consultation assistant. Please hold while we connect you.</Say>"
        '<Connect><Stream url="wss://{host}/api/voice/media-stream" /></Connect>'
        "</Response>"
    )
    return Response(content=twiml, media_type="application/xml")


@router.post("/outbound", response_model=OutboundCallResponse)
async def outbound_call(
    body: OutboundCallRequest,
    patient_workflow: PatientWorkflow = Depends(get_patient_workflow),
    twilio: TwilioAdapter = Depends(get_twilio_adapter),
):
    """Make an outbound call to a patient."""
    patient = await patient_workflow.get_patient(body.patient_id)
    if not patient.phone_number:
        return OutboundCallResponse(success=False, message="Patient has no phone number on file.")

    stream_url = "wss://{host}/api/voice/media-stream"
    call_sid = await twilio.make_outbound_call(to=patient.phone_number, stream_url=stream_url)
    return OutboundCallResponse(success=True, call_sid=call_sid)


@router.post("/token", response_model=VoiceTokenResponse)
async def get_voice_token(
    identity: str = Query(...),
    twilio: TwilioAdapter = Depends(get_twilio_adapter),
):
    """Generate a Twilio voice access token."""
    token = twilio.generate_voice_token(identity)
    return VoiceTokenResponse(token=token)


@router.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    """Bidirectional WebSocket bridge between Twilio and OpenAI Realtime."""
    await websocket.accept()

    openai_adapter = OpenAIRealtimeAdapter(system_instructions=SYSTEM_INSTRUCTIONS)
    stream_sid = None
    ai_speaking = False

    try:
        await openai_adapter.connect()

        async def receive_from_twilio():
            """Receive audio from Twilio and forward to OpenAI."""
            nonlocal stream_sid, ai_speaking
            try:
                while True:
                    data = await websocket.receive_text()
                    msg = json.loads(data)
                    event_type = msg.get("event")

                    if event_type == "start":
                        stream_sid = msg.get("start", {}).get("streamSid")
                        logger.info("Twilio stream started: %s", stream_sid)

                    elif event_type == "media":
                        # Mute caller audio while AI is speaking (don't forward to OpenAI)
                        if not ai_speaking:
                            audio_payload = msg["media"]["payload"]
                            await openai_adapter.send_audio(audio_payload)

                    elif event_type == "mark":
                        # Twilio finished playing audio; unmute
                        ai_speaking = False
                        logger.debug("Mark received, unmuting caller audio.")

                    elif event_type == "stop":
                        logger.info("Twilio stream stopped.")
                        break

            except WebSocketDisconnect:
                logger.info("Twilio WebSocket disconnected.")

        async def receive_from_openai():
            """Receive events from OpenAI and forward audio to Twilio."""
            nonlocal ai_speaking
            try:
                async for event in openai_adapter.receive():
                    event_type = event.get("type", "")

                    if event_type == "response.audio.delta":
                        # Forward audio to Twilio
                        ai_speaking = True
                        audio_delta = event.get("delta", "")
                        if audio_delta and stream_sid:
                            twilio_msg = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {"payload": audio_delta},
                            }
                            await websocket.send_text(json.dumps(twilio_msg))

                    elif event_type == "response.audio.done":
                        # Send mark to Twilio to know when audio playback finishes
                        if stream_sid:
                            mark_msg = {
                                "event": "mark",
                                "streamSid": stream_sid,
                                "mark": {"name": "ai_response_done"},
                            }
                            await websocket.send_text(json.dumps(mark_msg))

                    elif event_type == "input_audio_buffer.speech_started":
                        # User started speaking (if VAD is ever enabled)
                        ai_speaking = False

            except Exception:
                logger.exception("Error receiving from OpenAI.")

        # Run both tasks concurrently
        await asyncio.gather(receive_from_twilio(), receive_from_openai())

    except Exception:
        logger.exception("Error in media stream WebSocket.")
    finally:
        await openai_adapter.close()
