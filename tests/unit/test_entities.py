from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.entities.analytics_result_entity import AnalyticsResult
from app.domain.entities.conversation_entity import Conversation
from app.domain.entities.glucose_reading_entity import GlucoseReading
from app.domain.entities.medication_entity import Medication
from app.domain.entities.message_entity import Message
from app.domain.entities.patient_entity import Patient


class TestPatientEntity:
    def test_create_valid_patient(self):
        patient = Patient(
            id=uuid4(),
            firebase_uid="firebase123",
            first_name="John",
            last_name="Doe",
            diabetes_type="type1",
        )
        assert patient.first_name == "John"
        assert patient.diabetes_type == "type1"

    def test_create_patient_minimal_fields(self):
        patient = Patient(
            id=uuid4(),
            firebase_uid="uid",
            first_name="Jane",
            last_name="Smith",
        )
        assert patient.date_of_birth is None
        assert patient.diabetes_type is None

    def test_invalid_diabetes_type_raises(self):
        with pytest.raises(ValidationError):
            Patient(
                id=uuid4(),
                firebase_uid="uid",
                first_name="John",
                last_name="Doe",
                diabetes_type="invalid_type",
            )


class TestGlucoseReadingEntity:
    def test_create_valid_reading(self):
        reading = GlucoseReading(
            id=uuid4(),
            patient_id=uuid4(),
            reading_value=Decimal("120.5"),
            reading_type="cgm",
            recorded_at=datetime.now(),
        )
        assert reading.unit == "mg/dL"
        assert reading.reading_type == "cgm"

    def test_invalid_reading_type_raises(self):
        with pytest.raises(ValidationError):
            GlucoseReading(
                id=uuid4(),
                patient_id=uuid4(),
                reading_value=Decimal("120.5"),
                reading_type="invalid",
                recorded_at=datetime.now(),
            )


class TestMedicationEntity:
    def test_create_valid_medication(self):
        med = Medication(
            id=uuid4(),
            patient_id=uuid4(),
            name="Metformin",
            dosage="500mg",
            adherence_rate=Decimal("85.5"),
        )
        assert med.adherence_rate == Decimal("85.5")

    def test_adherence_rate_too_high_raises(self):
        with pytest.raises(ValidationError):
            Medication(
                id=uuid4(),
                patient_id=uuid4(),
                name="Metformin",
                adherence_rate=Decimal("101"),
            )

    def test_adherence_rate_negative_raises(self):
        with pytest.raises(ValidationError):
            Medication(
                id=uuid4(),
                patient_id=uuid4(),
                name="Metformin",
                adherence_rate=Decimal("-1"),
            )

    def test_adherence_rate_none_is_valid(self):
        med = Medication(
            id=uuid4(),
            patient_id=uuid4(),
            name="Insulin",
        )
        assert med.adherence_rate is None

    def test_adherence_rate_boundary_values(self):
        med_zero = Medication(id=uuid4(), patient_id=uuid4(), name="A", adherence_rate=Decimal("0"))
        assert med_zero.adherence_rate == Decimal("0")
        med_hundred = Medication(id=uuid4(), patient_id=uuid4(), name="B", adherence_rate=Decimal("100"))
        assert med_hundred.adherence_rate == Decimal("100")


class TestAnalyticsResultEntity:
    def test_create_valid(self):
        result = AnalyticsResult(
            id=uuid4(),
            patient_id=uuid4(),
            result_type="trend_analysis",
            result_data={"trend": "improving", "score": 85},
        )
        assert result.result_type == "trend_analysis"


class TestConversationEntity:
    def test_create_valid(self):
        conv = Conversation(
            id=uuid4(),
            patient_id=uuid4(),
            channel="web_chat",
        )
        assert conv.channel == "web_chat"

    def test_invalid_channel_raises(self):
        with pytest.raises(ValidationError):
            Conversation(
                id=uuid4(),
                patient_id=uuid4(),
                channel="email",
            )


class TestMessageEntity:
    def test_create_valid(self):
        msg = Message(
            id=uuid4(),
            conversation_id=uuid4(),
            role="user",
            content="Hello",
        )
        assert msg.role == "user"

    def test_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            Message(
                id=uuid4(),
                conversation_id=uuid4(),
                role="admin",
                content="Hello",
            )
