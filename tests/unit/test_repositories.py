from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.infrastructure.repositories.sql_analytics_repository import SQLAnalyticsRepository
from app.infrastructure.repositories.sql_conversation_repository import SQLConversationRepository
from app.infrastructure.repositories.sql_patient_repository import SQLPatientRepository


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


class TestSQLPatientRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_db):
        patient_id = 1
        mock_db.fetch_one.return_value = {
            "id": patient_id,
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": None,
            "diabetes_type": "type_2",
            "phone_number": None,
            "email": None,
            "created_at": datetime.now(),
            "updated_at": None,
        }
        repo = SQLPatientRepository(mock_db)
        patient = await repo.get_by_id(patient_id)
        assert patient is not None
        assert patient.id == patient_id
        assert patient.first_name == "John"
        mock_db.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db):
        mock_db.fetch_one.return_value = None
        repo = SQLPatientRepository(mock_db)
        result = await repo.get_by_id(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, mock_db):
        mock_db.fetch_all.return_value = [
            {
                "id": 1, "first_name": "A", "last_name": "B",
                "date_of_birth": None, "diabetes_type": None,
                "phone_number": None, "email": None,
                "created_at": None, "updated_at": None,
            },
            {
                "id": 2, "first_name": "C", "last_name": "D",
                "date_of_birth": None, "diabetes_type": "type_1",
                "phone_number": None, "email": None,
                "created_at": None, "updated_at": None,
            },
        ]
        repo = SQLPatientRepository(mock_db)
        patients = await repo.list_all()
        assert len(patients) == 2
        assert patients[0].id == 1

    @pytest.mark.asyncio
    async def test_get_glucose_readings(self, mock_db):
        patient_id = 1
        mock_db.fetch_all.return_value = [
            {
                "id": 1, "patient_id": patient_id,
                "value": Decimal("120.5"), "reading_type": "cgm",
                "unit": "mg/dL", "reading_timestamp": datetime.now(), "created_at": None,
            },
        ]
        repo = SQLPatientRepository(mock_db)
        readings = await repo.get_glucose_readings(patient_id, days=30)
        assert len(readings) == 1
        assert readings[0].value == Decimal("120.5")

    @pytest.mark.asyncio
    async def test_get_medications(self, mock_db):
        patient_id = 1
        mock_db.fetch_all.return_value = [
            {
                "id": 1, "patient_id": patient_id, "name": "Metformin",
                "dosage": "500mg", "frequency": "2x daily", "adherence_rate": Decimal("0.90"),
                "start_date": None, "end_date": None, "created_at": None,
            },
        ]
        repo = SQLPatientRepository(mock_db)
        meds = await repo.get_medications(patient_id)
        assert len(meds) == 1
        assert meds[0].name == "Metformin"


class TestSQLAnalyticsRepository:
    @pytest.mark.asyncio
    async def test_get_by_patient(self, mock_db):
        patient_id = 1
        mock_db.fetch_one.return_value = {
            "id": 1, "patient_id": patient_id,
            "risk_score": {"overall": 80}, "trend": {"direction": "improving"},
            "complication_flags": ["retinopathy_risk"],
            "computed_at": datetime.now(),
        }
        repo = SQLAnalyticsRepository(mock_db)
        result = await repo.get_by_patient(patient_id)
        assert result is not None
        assert result.risk_score == {"overall": 80}

    @pytest.mark.asyncio
    async def test_get_by_patient_not_found(self, mock_db):
        mock_db.fetch_one.return_value = None
        repo = SQLAnalyticsRepository(mock_db)
        result = await repo.get_by_patient(999)
        assert result is None


class TestSQLConversationRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_db):
        conv_id = 1
        mock_db.fetch_one.return_value = {
            "id": conv_id, "patient_id": 1, "channel": "web",
            "status": "active", "started_at": datetime.now(), "ended_at": None,
        }
        repo = SQLConversationRepository(mock_db)
        conv = await repo.get_by_id(conv_id)
        assert conv is not None
        assert conv.id == conv_id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db):
        mock_db.fetch_one.return_value = None
        repo = SQLConversationRepository(mock_db)
        result = await repo.get_by_id(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_messages(self, mock_db):
        conv_id = 1
        mock_db.fetch_all.return_value = [
            {
                "id": 1, "conversation_id": conv_id, "role": "user",
                "content": "Hello", "created_at": datetime.now(),
            },
        ]
        repo = SQLConversationRepository(mock_db)
        messages = await repo.get_messages(conv_id)
        assert len(messages) == 1
        assert messages[0].content == "Hello"
