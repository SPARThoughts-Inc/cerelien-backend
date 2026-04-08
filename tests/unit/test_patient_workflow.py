from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundException
from app.domain.entities.glucose_reading_entity import GlucoseReading
from app.domain.entities.medication_entity import Medication
from app.domain.entities.patient_entity import Patient
from app.domain.workflows.patient_workflow import PatientWorkflow


@pytest.fixture
def patient_repo():
    return AsyncMock()


@pytest.fixture
def analytics_repo():
    return AsyncMock()


@pytest.fixture
def workflow(patient_repo, analytics_repo):
    return PatientWorkflow(patient_repo=patient_repo, analytics_repo=analytics_repo)


@pytest.fixture
def sample_patient():
    return Patient(
        id=uuid4(),
        firebase_uid="uid123",
        first_name="John",
        last_name="Doe",
        diabetes_type="type2",
    )


class TestGetPatient:
    @pytest.mark.asyncio
    async def test_get_patient_success(self, workflow, patient_repo, sample_patient):
        patient_repo.get_by_id.return_value = sample_patient
        result = await workflow.get_patient(sample_patient.id)
        assert result.id == sample_patient.id
        patient_repo.get_by_id.assert_called_once_with(sample_patient.id)

    @pytest.mark.asyncio
    async def test_get_patient_not_found(self, workflow, patient_repo):
        patient_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundException):
            await workflow.get_patient(uuid4())


class TestListPatients:
    @pytest.mark.asyncio
    async def test_list_patients(self, workflow, patient_repo, sample_patient):
        patient_repo.list_all.return_value = [sample_patient]
        result = await workflow.list_patients()
        assert len(result) == 1


class TestGetSummary:
    @pytest.mark.asyncio
    async def test_get_summary_with_data(self, workflow, patient_repo, sample_patient):
        patient_repo.get_by_id.return_value = sample_patient

        # CGM readings
        cgm_readings = [
            GlucoseReading(
                id=uuid4(), patient_id=sample_patient.id,
                reading_value=Decimal("130"), reading_type="cgm",
                recorded_at=datetime.now(),
            ),
            GlucoseReading(
                id=uuid4(), patient_id=sample_patient.id,
                reading_value=Decimal("110"), reading_type="cgm",
                recorded_at=datetime.now(),
            ),
        ]

        # A1C reading
        a1c_readings = [
            GlucoseReading(
                id=uuid4(), patient_id=sample_patient.id,
                reading_value=Decimal("7.2"), reading_type="a1c",
                recorded_at=datetime.now(),
            ),
        ]

        # get_glucose_readings is called twice: once for cgm, once for a1c
        patient_repo.get_glucose_readings.side_effect = [cgm_readings, a1c_readings]

        summary = await workflow.get_summary(sample_patient.id)
        assert summary["patient"].id == sample_patient.id
        assert summary["latest_a1c"] == Decimal("7.2")
        assert summary["avg_glucose_30d"] == Decimal("120")  # (130+110)/2
        assert summary["active_alerts"] == []

    @pytest.mark.asyncio
    async def test_get_summary_high_a1c_alert(self, workflow, patient_repo, sample_patient):
        patient_repo.get_by_id.return_value = sample_patient

        a1c_readings = [
            GlucoseReading(
                id=uuid4(), patient_id=sample_patient.id,
                reading_value=Decimal("10.5"), reading_type="a1c",
                recorded_at=datetime.now(),
            ),
        ]
        patient_repo.get_glucose_readings.side_effect = [[], a1c_readings]

        summary = await workflow.get_summary(sample_patient.id)
        assert summary["latest_a1c"] == Decimal("10.5")
        assert "A1C critically high (>9.0%)" in summary["active_alerts"]

    @pytest.mark.asyncio
    async def test_get_summary_no_readings(self, workflow, patient_repo, sample_patient):
        patient_repo.get_by_id.return_value = sample_patient
        patient_repo.get_glucose_readings.side_effect = [[], []]

        summary = await workflow.get_summary(sample_patient.id)
        assert summary["latest_a1c"] is None
        assert summary["avg_glucose_30d"] is None
        assert summary["active_alerts"] == []

    @pytest.mark.asyncio
    async def test_get_summary_patient_not_found(self, workflow, patient_repo):
        patient_repo.get_by_id.return_value = None
        with pytest.raises(NotFoundException):
            await workflow.get_summary(uuid4())
