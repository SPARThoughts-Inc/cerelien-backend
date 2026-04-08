import logging

from app.domain.interfaces.conversation_repository import ConversationRepository
from app.domain.interfaces.patient_repository import PatientRepository
from app.domain.workflows.consultation_workflow import ConsultationWorkflow
from app.infrastructure.adapters.twilio_adapter import TwilioAdapter

logger = logging.getLogger(__name__)

MAX_SMS_LENGTH = 1600


class SMSWorkflow:
    def __init__(
        self,
        patient_repo: PatientRepository,
        consultation_workflow: ConsultationWorkflow,
        conversation_repo: ConversationRepository,
        twilio: TwilioAdapter,
    ):
        self.patient_repo = patient_repo
        self.consultation_workflow = consultation_workflow
        self.conversation_repo = conversation_repo
        self.twilio = twilio

    async def handle_incoming_sms(self, from_number: str, body: str) -> str:
        """Handle an incoming SMS from a patient. Returns the response text."""
        # Look up patient by phone number
        patient = await self.patient_repo.get_by_phone(from_number)
        if not patient:
            return "We could not find your account. Please register at our website or contact support."

        # Find or create an SMS conversation for this patient
        conversation_id = await self._get_or_create_sms_conversation(patient.id)

        # Run non-streaming chat
        response = await self.consultation_workflow.chat(
            patient_id=patient.id,
            conversation_id=conversation_id,
            user_message=body,
            channel="sms",
        )

        # Split long responses into multiple SMS segments
        segments = self._split_response(response)

        # Send additional segments via Twilio if more than one
        if len(segments) > 1:
            for segment in segments[1:]:
                await self.twilio.send_sms(to=from_number, body=segment)

        # Return first segment as TwiML reply
        return segments[0]

    async def _get_or_create_sms_conversation(self, patient_id: int) -> int:
        """Find an existing SMS conversation or create a new one."""
        conversations = await self.conversation_repo.get_patient_conversations(patient_id)
        for conv in conversations:
            if conv.channel == "sms" and conv.ended_at is None:
                return conv.id

        # Create new SMS conversation
        conversation = await self.consultation_workflow.start_conversation(patient_id, channel="sms")
        return conversation.id

    @staticmethod
    def _split_response(text: str) -> list[str]:
        """Split a long response into SMS-sized segments."""
        if len(text) <= MAX_SMS_LENGTH:
            return [text]

        segments = []
        while text:
            if len(text) <= MAX_SMS_LENGTH:
                segments.append(text)
                break
            # Find a good break point (last space before limit)
            break_point = text.rfind(" ", 0, MAX_SMS_LENGTH)
            if break_point == -1:
                break_point = MAX_SMS_LENGTH
            segments.append(text[:break_point])
            text = text[break_point:].lstrip()

        return segments
