"""Additional route tests for coverage."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_consultation_workflow, get_patient_workflow
from app.domain.entities.analytics_result_entity import AnalyticsResult
from app.domain.entities.conversation_entity import Conversation
from app.domain.entities.glucose_reading_entity import GlucoseReading
from app.domain.entities.medication_entity import Medication
from app.domain.entities.patient_entity import Patient
from app.domain.workflows.consultation_workflow import ConsultationWorkflow
from app.domain.workflows.patient_workflow import PatientWorkflow
from app.main import create_app


@pytest.fixture
def mock_patient_workflow():
    return AsyncMock(spec=PatientWorkflow)


@pytest.fixture
def mock_consultation_workflow():
    return AsyncMock(spec=ConsultationWorkflow)


@pytest.fixture
def app(mock_patient_workflow, mock_consultation_workflow):
    application = create_app()
    application.dependency_overrides[get_patient_workflow] = lambda: mock_patient_workflow
    application.dependency_overrides[get_consultation_workflow] = lambda: mock_consultation_workflow
    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestPatientGlucoseRoute:
    @pytest.mark.asyncio
    async def test_get_glucose_readings(self, client, mock_patient_workflow):
        patient_id = uuid4()
        mock_patient_workflow.get_glucose_readings.return_value = [
            GlucoseReading(
                id=uuid4(), patient_id=patient_id,
                reading_value=Decimal("120.5"), reading_type="cgm",
                unit="mg/dL", recorded_at=datetime.now(),
            ),
        ]
        response = await client.get(f"/api/patients/{patient_id}/glucose")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestPatientAnalyticsRoute:
    @pytest.mark.asyncio
    async def test_get_analytics(self, client, mock_patient_workflow):
        patient_id = uuid4()
        mock_patient_workflow.get_analytics.return_value = [
            AnalyticsResult(
                id=uuid4(), patient_id=patient_id,
                result_type="trend", result_data={"score": 85},
                generated_at=datetime.now(),
            ),
        ]
        response = await client.get(f"/api/patients/{patient_id}/analytics")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestPatientMedicationsRoute:
    @pytest.mark.asyncio
    async def test_get_medications(self, client, mock_patient_workflow):
        patient_id = uuid4()
        mock_patient_workflow.get_medications.return_value = [
            Medication(
                id=uuid4(), patient_id=patient_id,
                name="Metformin", dosage="500mg",
                frequency="2x daily", adherence_rate=Decimal("90"),
            ),
        ]
        response = await client.get(f"/api/patients/{patient_id}/medications")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Metformin"


class TestPatientSummaryRoute:
    @pytest.mark.asyncio
    async def test_get_summary(self, client, mock_patient_workflow):
        patient_id = uuid4()
        patient = Patient(
            id=patient_id, firebase_uid="uid1",
            first_name="John", last_name="Doe",
            created_at=datetime.now(),
        )

        async def mock_get_summary(pid):
            return {
                "patient": patient,
                "latest_a1c": Decimal("7.5"),
                "avg_glucose_30d": Decimal("130.5"),
                "active_alerts": [],
            }

        mock_patient_workflow.get_summary = mock_get_summary

        response = await client.get(f"/api/patients/{patient_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert float(data["latest_a1c"]) == 7.5


class TestChatStreamRoute:
    @pytest.mark.asyncio
    async def test_chat_stream_with_new_conversation(self, client, mock_consultation_workflow):
        patient_id = uuid4()
        conv_id = uuid4()
        mock_consultation_workflow.start_conversation.return_value = Conversation(
            id=conv_id, patient_id=patient_id, channel="web_chat",
        )

        async def mock_stream(*args, **kwargs):
            yield "Hello "
            yield "world"

        mock_consultation_workflow.chat_stream = mock_stream

        response = await client.post(
            f"/api/chat?patient_id={patient_id}",
            json={"message": "Hi there"},
        )
        assert response.status_code == 200
        assert "Hello " in response.text

    @pytest.mark.asyncio
    async def test_chat_stream_with_existing_conversation(self, client, mock_consultation_workflow):
        patient_id = uuid4()
        conv_id = uuid4()

        async def mock_stream(*args, **kwargs):
            yield "Response"

        mock_consultation_workflow.chat_stream = mock_stream

        response = await client.post(
            f"/api/chat?patient_id={patient_id}",
            json={"message": "Hi", "conversation_id": str(conv_id)},
        )
        assert response.status_code == 200
