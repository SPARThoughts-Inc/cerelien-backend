from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_patient_workflow
from app.core.exceptions import NotFoundException
from app.domain.entities.patient_entity import Patient
from app.domain.workflows.patient_workflow import PatientWorkflow
from app.main import create_app


@pytest.fixture
def mock_workflow():
    return AsyncMock(spec=PatientWorkflow)


@pytest.fixture
def app(mock_workflow):
    application = create_app()
    application.dependency_overrides[get_patient_workflow] = lambda: mock_workflow
    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_patient():
    return Patient(
        id=1,
        first_name="John",
        last_name="Doe",
        diabetes_type="type_2",
        created_at=datetime.now(),
    )


class TestListPatients:
    @pytest.mark.asyncio
    async def test_list_patients(self, client, mock_workflow, sample_patient):
        mock_workflow.list_patients.return_value = [sample_patient]
        response = await client.get("/api/patients")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["patients"][0]["first_name"] == "John"

    @pytest.mark.asyncio
    async def test_list_patients_empty(self, client, mock_workflow):
        mock_workflow.list_patients.return_value = []
        response = await client.get("/api/patients")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["patients"] == []


class TestGetPatient:
    @pytest.mark.asyncio
    async def test_get_patient_success(self, client, mock_workflow, sample_patient):
        mock_workflow.get_patient.return_value = sample_patient
        response = await client.get(f"/api/patients/{sample_patient.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"

    @pytest.mark.asyncio
    async def test_get_patient_not_found(self, client, mock_workflow):
        mock_workflow.get_patient.side_effect = NotFoundException("Patient not found")
        response = await client.get("/api/patients/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Patient not found"
