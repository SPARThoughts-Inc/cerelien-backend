import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from twilio.rest import Client

from app.api.deps import db, get_patient_workflow, get_twilio_adapter
from app.core.config import settings
from app.domain.workflows.patient_workflow import PatientWorkflow
from app.infrastructure.adapters.openai_realtime_adapter import OpenAIRealtimeAdapter
from app.infrastructure.adapters.twilio_adapter import TwilioAdapter
from app.infrastructure.repositories.sql_analytics_repository import SQLAnalyticsRepository
from app.infrastructure.repositories.sql_patient_repository import SQLPatientRepository
from app.schemas.voice_schemas import OutboundCallRequest, OutboundCallResponse, VoiceTokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

SYSTEM_INSTRUCTIONS = """You are a compassionate diabetes care consultant at Cerelien AI. Your voice should radiate warmth and genuine sympathy throughout every interaction.

Your approach:
- Listen with empathy. Acknowledge the patient's feelings before jumping to clinical advice.
- Speak slowly, clearly, and with kindness — many callers may be elderly or anxious about their health.
- Use encouraging language: "That's a great question", "You're doing the right thing by reaching out", "I'm glad you asked about that."
- Explain medical concepts in simple, everyday language. Avoid jargon.
- When discussing glucose readings or A1C results, frame them positively when possible: "Your A1C has improved — that's wonderful progress."
- For concerning results, be honest but gentle: "I want to be upfront with you — this reading suggests we should pay extra attention to..."
- Always end with actionable, hopeful guidance.

Clinical focus areas:
- Glucose management education (what readings mean, target ranges, time-in-range)
- Medication adherence coaching (gentle reminders, addressing barriers)
- Lifestyle guidance (diet, exercise, stress management)
- Complication prevention and early warning signs

Safety: If the patient describes emergency symptoms (severe hypoglycemia below 54 mg/dL, signs of DKA like fruity breath/vomiting/confusion, chest pain, or stroke symptoms), calmly but firmly advise calling 911 immediately.

Remember: You are often the only accessible healthcare guidance these patients have. Treat every caller with the dignity, patience, and warmth they deserve."""


@router.post("/incoming")
async def incoming_call(request: Request):
    """Handle incoming Twilio voice call. Returns simple TwiML — patient lookup happens in WebSocket."""
    domain = settings.server_domain
    scheme = "wss" if domain != "localhost" else "ws"
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Connect><Stream url="{scheme}://{domain}/api/voice/media-stream" /></Connect>'
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

    domain = settings.server_domain
    scheme = "wss" if domain != "localhost" else "ws"
    stream_url = f"{scheme}://{domain}/api/voice/media-stream"
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


async def _build_patient_context(call_sid: str) -> str:
    """Look up the caller via Twilio call API, then fetch their patient data from DB."""
    # Get caller number from Twilio
    caller_number = ""
    try:
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        call = client.calls(call_sid).fetch()
        caller_number = call._from
        logger.info("Caller number from Twilio: %s", caller_number)
    except Exception as e:
        logger.warning("Could not fetch call info from Twilio: %s", e)
        return (
            "\n\nCould not identify the caller. Greet them warmly: "
            "'Hello, thank you for calling Cerelien! I'm your diabetes care consultant. How can I help you today?'"
        )

    # Look up patient
    patient_repo = SQLPatientRepository(db)
    analytics_repo = SQLAnalyticsRepository(db)
    patient = await patient_repo.get_by_phone(caller_number)

    if not patient:
        logger.info("No patient found for %s", caller_number)
        return (
            "\n\nThe caller is not in our system. Greet them warmly: "
            "'Hello, thank you for calling Cerelien! I'm your diabetes care consultant. How can I help you today?'"
        )

    first_name = patient.first_name
    patient_name = f"{patient.first_name} {patient.last_name}"
    logger.info("Identified patient: %s (ID: %s)", patient_name, patient.id)

    # Fetch health data
    readings = await patient_repo.get_glucose_readings(patient.id, days=30)
    meds = await patient_repo.get_medications(patient.id)
    analytics = await analytics_repo.get_by_patient(patient.id)

    cgm = [r for r in readings if r.reading_type == "cgm"]
    a1c = [r for r in readings if r.reading_type == "a1c"]
    avg_glucose = round(sum(float(r.value) for r in cgm) / len(cgm), 1) if cgm else None
    latest_a1c = float(a1c[0].value) if a1c else None

    med_list = ", ".join(f"{m.name} {m.dosage} ({m.frequency})" for m in meds) if meds else "None on file"

    risk_info = ""
    if analytics and analytics.risk_score:
        rs = analytics.risk_score
        risk_info = f"Risk scores — Overall: {rs.get('overall', 'N/A')}, Cardiovascular: {rs.get('cardiovascular', 'N/A')}, Nephropathy: {rs.get('nephropathy', 'N/A')}, Retinopathy: {rs.get('retinopathy', 'N/A')}"

    trend_info = ""
    if analytics and analytics.trend:
        t = analytics.trend
        tir = round(float(t.get("time_in_range", 0)) * 100, 1)
        trend_info = f"Glucose trend: {t.get('direction', 'N/A')}, Avg glucose: {t.get('avg_glucose', 'N/A')} mg/dL, Time in range: {tir}%"

    flags = ""
    if analytics and analytics.complication_flags:
        flags = f"Active complication flags: {', '.join(analytics.complication_flags)}"
    else:
        flags = "No active complication flags"

    return (
        f"\n\nPATIENT ON THE LINE:\n"
        f"Name: {patient_name}\n"
        f"Diabetes type: {patient.diabetes_type.replace('_', ' ')}\n"
        f"Date of birth: {patient.date_of_birth}\n"
        f"Latest A1C: {latest_a1c}%\n"
        f"Average glucose (30 days): {avg_glucose} mg/dL\n"
        f"Medications: {med_list}\n"
        f"{risk_info}\n{trend_info}\n{flags}\n\n"
        f"GREETING: You must greet them warmly by first name. Say something like: "
        f"'Hello {first_name}, welcome back to Cerelien! It is so good to hear from you. "
        f"How can I help you with your diabetes care today?'\n"
        f"You have their full health data above. When they ask about their readings, medications, "
        f"or risk factors, reference this data specifically and explain what it means for them."
    )


@router.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    """Bidirectional WebSocket bridge between Twilio and OpenAI Realtime.

    Flow:
    1. Twilio connects and sends 'start' event with callSid
    2. We look up the caller via Twilio API → get phone number → query patient DB
    3. Build personalized instructions with patient health data
    4. Connect to OpenAI Realtime with those instructions
    5. Trigger AI to greet the patient
    6. Bridge audio bidirectionally
    """
    await websocket.accept()
    logger.info("Twilio WebSocket accepted")

    stream_sid: str | None = None
    ai_speaking = False
    openai_adapter: OpenAIRealtimeAdapter | None = None
    openai_ready = asyncio.Event()

    async def receive_from_twilio():
        nonlocal stream_sid, ai_speaking, openai_adapter
        try:
            while True:
                data = await websocket.receive_text()
                msg = json.loads(data)
                event_type = msg.get("event")

                if event_type == "start":
                    stream_sid = msg["start"]["streamSid"]
                    call_sid = msg["start"].get("callSid", "")
                    logger.info("Stream started (streamSid=%s, callSid=%s)", stream_sid, call_sid)

                    # Look up patient data and connect to OpenAI
                    patient_context = await _build_patient_context(call_sid)
                    instructions = SYSTEM_INSTRUCTIONS + patient_context

                    openai_adapter = OpenAIRealtimeAdapter(system_instructions=instructions)
                    await openai_adapter.connect()
                    logger.info("OpenAI Realtime connected with patient context")
                    openai_ready.set()

                elif event_type == "media":
                    if openai_adapter and not ai_speaking:
                        await openai_adapter.send_audio(msg["media"]["payload"])

                elif event_type == "mark":
                    ai_speaking = False

                elif event_type == "stop":
                    logger.info("Twilio stream stopped")
                    break

        except WebSocketDisconnect:
            logger.info("Twilio disconnected")
        except Exception:
            logger.exception("Error in Twilio receiver")

    async def receive_from_openai():
        nonlocal ai_speaking
        # Wait until OpenAI is connected
        await openai_ready.wait()
        logger.info("OpenAI ready — starting audio bridge")

        try:
            async for event in openai_adapter.receive():
                event_type = event.get("type", "")

                if event_type == "error":
                    logger.error("OpenAI error: %s", event)

                elif event_type == "session.updated":
                    # Session configured — trigger the greeting
                    logger.info("Session configured — triggering AI greeting")
                    await openai_adapter.send_response_create()

                elif event_type == "response.audio.delta":
                    ai_speaking = True
                    audio = event.get("delta", "")
                    if audio and stream_sid:
                        await websocket.send_text(json.dumps({
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": audio},
                        }))

                elif event_type == "response.audio.done":
                    if stream_sid:
                        await websocket.send_text(json.dumps({
                            "event": "mark",
                            "streamSid": stream_sid,
                            "mark": {"name": "ai_done"},
                        }))

                elif event_type == "input_audio_buffer.speech_started":
                    ai_speaking = False

        except Exception:
            logger.exception("Error in OpenAI receiver")

    try:
        await asyncio.gather(receive_from_twilio(), receive_from_openai())
    except Exception:
        logger.exception("Error in media stream")
    finally:
        if openai_adapter:
            await openai_adapter.close()
        logger.info("Voice session ended")
