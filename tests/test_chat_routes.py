"""Tests for chat routes."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_consultation_workflow
from app.domain.entities.conversation_entity import Conversation
from app.domain.workflows.consultation_workflow import ConsultationWorkflow
from app.main import create_app


@pytest.fixture
def mock_workflow():
    return AsyncMock(spec=ConsultationWorkflow)


@pytest.fixture
def app(mock_workflow):
    application = create_app()
    application.dependency_overrides[get_consultation_workflow] = lambda: mock_workflow
    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestStartChat:
    @pytest.mark.asyncio
    async def test_start_chat_returns_conversation_id(self, client, mock_workflow):
        conv_id = 10
        patient_id = 1
        mock_workflow.start_conversation.return_value = Conversation(
            id=conv_id, patient_id=patient_id, channel="web"
        )

        response = await client.post(f"/api/chat/start?patient_id={patient_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conv_id
        mock_workflow.start_conversation.assert_called_once()
