"""Tests for agent tool functions."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domain.business_process.agents.context import ConsultationContext
from app.domain.business_process.agents.tools import (
    get_analytics_results,
    get_medications,
    get_patient_glucose_data,
    get_patient_profile,
)
from app.domain.entities.analytics_result_entity import AnalyticsResult
from app.domain.entities.glucose_reading_entity import GlucoseReading
from app.domain.entities.medication_entity import Medication
from app.domain.entities.patient_entity import Patient


@pytest.fixture
def patient_workflow():
    return AsyncMock()


@pytest.fixture
def context(patient_workflow):
    return ConsultationContext(
        patient_id=str(uuid4()),
        patient_workflow=patient_workflow,
        channel="web_chat",
    )


@pytest.fixture
def ctx_wrapper(context):
    """Create a mock RunContextWrapper."""
    wrapper = MagicMock()
    wrapper.context = context
    return wrapper


class TestGetPatientProfile:
    @pytest.mark.asyncio
    async def test_returns_formatted_profile(self, ctx_wrapper, patient_workflow):
        patient = Patient(
            id=uuid4(),
            firebase_uid="uid1",
            first_name="Jane",
            last_name="Smith",
            diabetes_type="type1",
            date_of_birth=datetime(1990, 5, 15).date(),
            diagnosis_date=datetime(2020, 1, 1).date(),
            phone_number="+15551234567",
        )
        patient_workflow.get_patient.return_value = patient

        # Call the underlying function directly
        result = await get_patient_profile.on_invoke_tool(ctx_wrapper, "")

        assert "Jane Smith" in result
        assert "type1" in result
        assert "+15551234567" in result


class TestGetPatientGlucoseData:
    @pytest.mark.asyncio
    async def test_no_readings(self, ctx_wrapper, patient_workflow):
        patient_workflow.get_glucose_readings.return_value = []

        result = await get_patient_glucose_data.on_invoke_tool(ctx_wrapper, "{}")

        assert "No glucose readings found" in result

    @pytest.mark.asyncio
    async def test_with_a1c_and_cgm_readings(self, ctx_wrapper, patient_workflow):
        patient_id = uuid4()
        readings = [
            GlucoseReading(
                id=uuid4(), patient_id=patient_id,
                reading_value=Decimal("7.2"), reading_type="a1c",
                unit="%", recorded_at=datetime.now(),
            ),
            GlucoseReading(
                id=uuid4(), patient_id=patient_id,
                reading_value=Decimal("120"), reading_type="cgm",
                unit="mg/dL", recorded_at=datetime.now(),
            ),
            GlucoseReading(
                id=uuid4(), patient_id=patient_id,
                reading_value=Decimal("150"), reading_type="cgm",
                unit="mg/dL", recorded_at=datetime.now(),
            ),
        ]
        patient_workflow.get_glucose_readings.return_value = readings

        result = await get_patient_glucose_data.on_invoke_tool(ctx_wrapper, '{"days": 30}')

        assert "A1C: 7.2%" in result
        assert "Average Glucose" in result
        assert "Time in Range" in result

    @pytest.mark.asyncio
    async def test_only_a1c_readings(self, ctx_wrapper, patient_workflow):
        patient_id = uuid4()
        readings = [
            GlucoseReading(
                id=uuid4(), patient_id=patient_id,
                reading_value=Decimal("8.5"), reading_type="a1c",
                unit="%", recorded_at=datetime.now(),
            ),
        ]
        patient_workflow.get_glucose_readings.return_value = readings

        result = await get_patient_glucose_data.on_invoke_tool(ctx_wrapper, '{"days": 30}')

        assert "A1C: 8.5%" in result


class TestGetAnalyticsResults:
    @pytest.mark.asyncio
    async def test_no_results(self, ctx_wrapper, patient_workflow):
        patient_workflow.get_analytics.return_value = []

        result = await get_analytics_results.on_invoke_tool(ctx_wrapper, "")

        assert "No analytics results available" in result

    @pytest.mark.asyncio
    async def test_with_results(self, ctx_wrapper, patient_workflow):
        patient_id = uuid4()
        results = [
            AnalyticsResult(
                id=uuid4(), patient_id=patient_id,
                result_type="trend",
                result_data={"direction": "improving", "score": 85},
                generated_at=datetime.now(),
            ),
        ]
        patient_workflow.get_analytics.return_value = results

        result = await get_analytics_results.on_invoke_tool(ctx_wrapper, "")

        assert "trend" in result
        assert "improving" in result


class TestGetMedications:
    @pytest.mark.asyncio
    async def test_no_medications(self, ctx_wrapper, patient_workflow):
        patient_workflow.get_medications.return_value = []

        result = await get_medications.on_invoke_tool(ctx_wrapper, "")

        assert "No medications on record" in result

    @pytest.mark.asyncio
    async def test_with_medications(self, ctx_wrapper, patient_workflow):
        patient_id = uuid4()
        meds = [
            Medication(
                id=uuid4(), patient_id=patient_id,
                name="Metformin", dosage="500mg",
                frequency="2x daily", adherence_rate=Decimal("90"),
            ),
            Medication(
                id=uuid4(), patient_id=patient_id,
                name="Insulin", dosage=None,
                frequency=None, adherence_rate=None,
            ),
        ]
        patient_workflow.get_medications.return_value = meds

        result = await get_medications.on_invoke_tool(ctx_wrapper, "")

        assert "Metformin" in result
        assert "500mg" in result
        assert "90%" in result
        assert "Insulin" in result
        assert "N/A" in result
