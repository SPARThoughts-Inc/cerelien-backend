"""Tests for voice routes."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_patient_workflow, get_twilio_adapter
from app.domain.entities.patient_entity import Patient
from app.domain.workflows.patient_workflow import PatientWorkflow
from app.infrastructure.adapters.twilio_adapter import TwilioAdapter
from app.main import create_app


@pytest.fixture
def mock_patient_workflow():
    return AsyncMock(spec=PatientWorkflow)


@pytest.fixture
def mock_twilio():
    mock = AsyncMock(spec=TwilioAdapter)
    mock.generate_voice_token = MagicMock(return_value="mock-jwt-token")
    return mock


@pytest.fixture
def app(mock_patient_workflow, mock_twilio):
    application = create_app()
    application.dependency_overrides[get_patient_workflow] = lambda: mock_patient_workflow
    application.dependency_overrides[get_twilio_adapter] = lambda: mock_twilio
    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestIncomingCall:
    @pytest.mark.asyncio
    async def test_incoming_returns_twiml(self, client):
        response = await client.post("/api/voice/incoming")
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "<Response>" in response.text
        assert "<Say>" in response.text
        assert "<Connect>" in response.text


class TestOutboundCall:
    @pytest.mark.asyncio
    async def test_outbound_returns_call_sid(self, client, mock_patient_workflow, mock_twilio):
        patient_id = 1
        mock_patient_workflow.get_patient.return_value = Patient(
            id=patient_id,
            first_name="John",
            last_name="Doe",
            phone_number="+15551234567",
        )
        mock_twilio.make_outbound_call.return_value = "CA1234567890"

        response = await client.post(
            "/api/voice/outbound",
            json={"patient_id": patient_id, "reason": "Follow-up"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["call_sid"] == "CA1234567890"

    @pytest.mark.asyncio
    async def test_outbound_no_phone_number(self, client, mock_patient_workflow):
        patient_id = 1
        mock_patient_workflow.get_patient.return_value = Patient(
            id=patient_id,
            first_name="John",
            last_name="Doe",
            phone_number=None,
        )

        response = await client.post(
            "/api/voice/outbound",
            json={"patient_id": patient_id, "reason": "Follow-up"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestVoiceToken:
    @pytest.mark.asyncio
    async def test_token_endpoint(self, client, mock_twilio):
        response = await client.post("/api/voice/token?identity=user123")
        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "mock-jwt-token"
