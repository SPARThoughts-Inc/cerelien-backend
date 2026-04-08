from datetime import datetime
from decimal import Decimal

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
            id=1,
            first_name="John",
            last_name="Doe",
            diabetes_type="type_1",
        )
        assert patient.first_name == "John"
        assert patient.diabetes_type == "type_1"

    def test_create_patient_minimal_fields(self):
        patient = Patient(
            id=2,
            first_name="Jane",
            last_name="Smith",
        )
        assert patient.date_of_birth is None
        assert patient.diabetes_type is None

    def test_invalid_diabetes_type_raises(self):
        with pytest.raises(ValidationError):
            Patient(
                id=3,
                first_name="John",
                last_name="Doe",
                diabetes_type="invalid_type",
            )


class TestGlucoseReadingEntity:
    def test_create_valid_reading(self):
        reading = GlucoseReading(
            id=1,
            patient_id=1,
            value=Decimal("120.5"),
            reading_type="cgm",
            reading_timestamp=datetime.now(),
        )
        assert reading.unit == "mg/dL"
        assert reading.reading_type == "cgm"

    def test_invalid_reading_type_raises(self):
        with pytest.raises(ValidationError):
            GlucoseReading(
                id=1,
                patient_id=1,
                value=Decimal("120.5"),
                reading_type="invalid",
                reading_timestamp=datetime.now(),
            )


class TestMedicationEntity:
    def test_create_valid_medication(self):
        med = Medication(
            id=1,
            patient_id=1,
            name="Metformin",
            dosage="500mg",
            adherence_rate=Decimal("0.85"),
        )
        assert med.adherence_rate == Decimal("0.85")

    def test_adherence_rate_too_high_raises(self):
        with pytest.raises(ValidationError):
            Medication(
                id=1,
                patient_id=1,
                name="Metformin",
                adherence_rate=Decimal("1.01"),
            )

    def test_adherence_rate_negative_raises(self):
        with pytest.raises(ValidationError):
            Medication(
                id=1,
                patient_id=1,
                name="Metformin",
                adherence_rate=Decimal("-0.01"),
            )

    def test_adherence_rate_none_is_valid(self):
        med = Medication(
            id=1,
            patient_id=1,
            name="Insulin",
        )
        assert med.adherence_rate is None

    def test_adherence_rate_boundary_values(self):
        med_zero = Medication(id=1, patient_id=1, name="A", adherence_rate=Decimal("0"))
        assert med_zero.adherence_rate == Decimal("0")
        med_one = Medication(id=2, patient_id=1, name="B", adherence_rate=Decimal("1.00"))
        assert med_one.adherence_rate == Decimal("1.00")


class TestAnalyticsResultEntity:
    def test_create_valid(self):
        result = AnalyticsResult(
            id=1,
            patient_id=1,
            risk_score={"overall": 85},
            trend={"direction": "improving"},
            complication_flags=["retinopathy_risk"],
        )
        assert result.risk_score == {"overall": 85}


class TestConversationEntity:
    def test_create_valid(self):
        conv = Conversation(
            id=1,
            patient_id=1,
            channel="web",
        )
        assert conv.channel == "web"

    def test_invalid_channel_raises(self):
        with pytest.raises(ValidationError):
            Conversation(
                id=1,
                patient_id=1,
                channel="email",
            )


class TestMessageEntity:
    def test_create_valid(self):
        msg = Message(
            id=1,
            conversation_id=1,
            role="user",
            content="Hello",
        )
        assert msg.role == "user"

    def test_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            Message(
                id=1,
                conversation_id=1,
                role="admin",
                content="Hello",
            )
