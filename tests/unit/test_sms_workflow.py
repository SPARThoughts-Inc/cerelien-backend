"""Tests for SMSWorkflow."""

from unittest.mock import AsyncMock

import pytest

from app.domain.entities.conversation_entity import Conversation
from app.domain.entities.patient_entity import Patient
from app.domain.workflows.sms_workflow import SMSWorkflow, MAX_SMS_LENGTH


@pytest.fixture
def patient_repo():
    return AsyncMock()


@pytest.fixture
def consultation_workflow():
    return AsyncMock()


@pytest.fixture
def conversation_repo():
    return AsyncMock()


@pytest.fixture
def twilio():
    return AsyncMock()


@pytest.fixture
def workflow(patient_repo, consultation_workflow, conversation_repo, twilio):
    return SMSWorkflow(
        patient_repo=patient_repo,
        consultation_workflow=consultation_workflow,
        conversation_repo=conversation_repo,
        twilio=twilio,
    )


class TestHandleIncomingSMS:
    @pytest.mark.asyncio
    async def test_patient_not_found(self, workflow, patient_repo):
        patient_repo.get_by_phone.return_value = None

        result = await workflow.handle_incoming_sms("+15551234567", "Hello")

        assert "could not find your account" in result.lower()

    @pytest.mark.asyncio
    async def test_patient_found_single_segment(
        self, workflow, patient_repo, consultation_workflow, conversation_repo
    ):
        patient_id = 1
        conv_id = 10
        patient = Patient(id=patient_id, first_name="A", last_name="B", phone_number="+15551234567")
        patient_repo.get_by_phone.return_value = patient

        # Existing SMS conversation
        conversation_repo.get_patient_conversations.return_value = [
            Conversation(id=conv_id, patient_id=patient_id, channel="sms"),
        ]
        consultation_workflow.chat.return_value = "Your glucose is fine."

        result = await workflow.handle_incoming_sms("+15551234567", "How's my glucose?")

        assert result == "Your glucose is fine."
        consultation_workflow.chat.assert_called_once_with(
            patient_id=patient_id,
            conversation_id=conv_id,
            user_message="How's my glucose?",
            channel="sms",
        )

    @pytest.mark.asyncio
    async def test_creates_new_conversation_if_none_exists(
        self, workflow, patient_repo, consultation_workflow, conversation_repo
    ):
        patient_id = 1
        conv_id = 10
        patient = Patient(id=patient_id, first_name="A", last_name="B")
        patient_repo.get_by_phone.return_value = patient
        conversation_repo.get_patient_conversations.return_value = []
        new_conv = Conversation(id=conv_id, patient_id=patient_id, channel="sms")
        consultation_workflow.start_conversation.return_value = new_conv
        consultation_workflow.chat.return_value = "Welcome!"

        result = await workflow.handle_incoming_sms("+15551234567", "Hi")

        assert result == "Welcome!"
        consultation_workflow.start_conversation.assert_called_once_with(patient_id, channel="sms")

    @pytest.mark.asyncio
    async def test_multi_segment_response(
        self, workflow, patient_repo, consultation_workflow, conversation_repo, twilio
    ):
        patient_id = 1
        conv_id = 10
        patient = Patient(id=patient_id, first_name="A", last_name="B", phone_number="+15551234567")
        patient_repo.get_by_phone.return_value = patient
        conversation_repo.get_patient_conversations.return_value = [
            Conversation(id=conv_id, patient_id=patient_id, channel="sms"),
        ]
        # Create a very long response
        long_response = "word " * 500  # Well over 1600 chars
        consultation_workflow.chat.return_value = long_response

        result = await workflow.handle_incoming_sms("+15551234567", "Tell me everything")

        # First segment returned, additional segments sent via Twilio
        assert len(result) <= MAX_SMS_LENGTH
        twilio.send_sms.assert_called()


class TestSplitResponse:
    def test_short_message(self):
        result = SMSWorkflow._split_response("Short message")
        assert result == ["Short message"]

    def test_long_message_splits(self):
        text = "word " * 500
        result = SMSWorkflow._split_response(text)
        assert len(result) > 1
        for segment in result:
            assert len(segment) <= MAX_SMS_LENGTH

    def test_no_space_break_point(self):
        # A single long word longer than MAX_SMS_LENGTH
        text = "x" * (MAX_SMS_LENGTH + 100)
        result = SMSWorkflow._split_response(text)
        assert len(result) > 1

    def test_exact_length(self):
        text = "a" * MAX_SMS_LENGTH
        result = SMSWorkflow._split_response(text)
        assert result == [text]
