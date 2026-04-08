"""Tests for ConsultationWorkflow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.entities.conversation_entity import Conversation
from app.domain.entities.message_entity import Message
from app.domain.workflows.consultation_workflow import ConsultationWorkflow


@pytest.fixture
def conversation_repo():
    return AsyncMock()


@pytest.fixture
def patient_workflow():
    return AsyncMock()


@pytest.fixture
def workflow(conversation_repo, patient_workflow):
    return ConsultationWorkflow(
        conversation_repo=conversation_repo,
        patient_workflow=patient_workflow,
    )


class TestStartConversation:
    @pytest.mark.asyncio
    async def test_start_conversation_creates_and_returns(self, workflow, conversation_repo):
        patient_id = 1
        expected_conv = Conversation(id=10, patient_id=patient_id, channel="web")
        conversation_repo.create.return_value = expected_conv

        result = await workflow.start_conversation(patient_id, "web")

        assert result.patient_id == patient_id
        assert result.channel == "web"
        conversation_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_conversation_sms_channel(self, workflow, conversation_repo):
        patient_id = 1
        expected_conv = Conversation(id=11, patient_id=patient_id, channel="sms")
        conversation_repo.create.return_value = expected_conv

        result = await workflow.start_conversation(patient_id, "sms")

        assert result.channel == "sms"


class TestChat:
    @pytest.mark.asyncio
    @patch("app.domain.workflows.consultation_workflow.Runner")
    async def test_chat_saves_two_messages(self, mock_runner_cls, workflow, conversation_repo):
        patient_id = 1
        conversation_id = 10

        # Mock Runner.run result
        mock_result = MagicMock()
        mock_result.final_output = "Here is my response about glucose."
        mock_result.last_agent = MagicMock()
        mock_result.last_agent.name = "Glucose Analysis Specialist"
        mock_runner_cls.run = AsyncMock(return_value=mock_result)

        # Mock get_messages to return empty history
        conversation_repo.get_messages.return_value = []

        response = await workflow.chat(patient_id, conversation_id, "Tell me about my glucose")

        assert response == "Here is my response about glucose."

        # Should have saved 2 messages: user + assistant
        assert conversation_repo.add_message.call_count == 2

        # First call: user message
        user_msg = conversation_repo.add_message.call_args_list[0][0][0]
        assert user_msg.role == "user"
        assert user_msg.content == "Tell me about my glucose"

        # Second call: assistant message
        assistant_msg = conversation_repo.add_message.call_args_list[1][0][0]
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "Here is my response about glucose."
