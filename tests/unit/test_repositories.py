from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

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
        patient_id = uuid4()
        mock_db.fetch_one.return_value = {
            "id": patient_id,
            "firebase_uid": "uid123",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": None,
            "diabetes_type": "type2",
            "diagnosis_date": None,
            "phone_number": None,
            "created_at": datetime.now(),
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
        result = await repo.get_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self, mock_db):
        pid1, pid2 = uuid4(), uuid4()
        mock_db.fetch_all.return_value = [
            {
                "id": pid1, "firebase_uid": "uid1", "first_name": "A", "last_name": "B",
                "date_of_birth": None, "diabetes_type": None, "diagnosis_date": None,
                "phone_number": None, "created_at": None,
            },
            {
                "id": pid2, "firebase_uid": "uid2", "first_name": "C", "last_name": "D",
                "date_of_birth": None, "diabetes_type": "type1", "diagnosis_date": None,
                "phone_number": None, "created_at": None,
            },
        ]
        repo = SQLPatientRepository(mock_db)
        patients = await repo.list_all()
        assert len(patients) == 2
        assert patients[0].id == pid1

    @pytest.mark.asyncio
    async def test_get_glucose_readings(self, mock_db):
        patient_id = uuid4()
        reading_id = uuid4()
        mock_db.fetch_all.return_value = [
            {
                "id": reading_id, "patient_id": patient_id,
                "reading_value": Decimal("120.5"), "reading_type": "cgm",
                "unit": "mg/dL", "recorded_at": datetime.now(), "created_at": None,
            },
        ]
        repo = SQLPatientRepository(mock_db)
        readings = await repo.get_glucose_readings(patient_id, days=30)
        assert len(readings) == 1
        assert readings[0].reading_value == Decimal("120.5")

    @pytest.mark.asyncio
    async def test_get_medications(self, mock_db):
        patient_id = uuid4()
        mock_db.fetch_all.return_value = [
            {
                "id": uuid4(), "patient_id": patient_id, "name": "Metformin",
                "dosage": "500mg", "frequency": "2x daily", "adherence_rate": Decimal("90"),
            },
        ]
        repo = SQLPatientRepository(mock_db)
        meds = await repo.get_medications(patient_id)
        assert len(meds) == 1
        assert meds[0].name == "Metformin"


class TestSQLAnalyticsRepository:
    @pytest.mark.asyncio
    async def test_get_by_patient(self, mock_db):
        patient_id = uuid4()
        mock_db.fetch_all.return_value = [
            {
                "id": uuid4(), "patient_id": patient_id, "result_type": "trend",
                "result_data": {"score": 80}, "generated_at": datetime.now(),
            },
        ]
        repo = SQLAnalyticsRepository(mock_db)
        results = await repo.get_by_patient(patient_id)
        assert len(results) == 1
        assert results[0].result_type == "trend"

    @pytest.mark.asyncio
    async def test_get_by_type(self, mock_db):
        patient_id = uuid4()
        mock_db.fetch_all.return_value = []
        repo = SQLAnalyticsRepository(mock_db)
        results = await repo.get_by_type(patient_id, "nonexistent")
        assert results == []


class TestSQLConversationRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, mock_db):
        conv_id = uuid4()
        mock_db.fetch_one.return_value = {
            "id": conv_id, "patient_id": uuid4(), "channel": "web_chat",
            "started_at": datetime.now(), "ended_at": None,
        }
        repo = SQLConversationRepository(mock_db)
        conv = await repo.get_by_id(conv_id)
        assert conv is not None
        assert conv.id == conv_id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db):
        mock_db.fetch_one.return_value = None
        repo = SQLConversationRepository(mock_db)
        result = await repo.get_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_messages(self, mock_db):
        conv_id = uuid4()
        mock_db.fetch_all.return_value = [
            {
                "id": uuid4(), "conversation_id": conv_id, "role": "user",
                "agent_name": None, "content": "Hello", "created_at": datetime.now(),
            },
        ]
        repo = SQLConversationRepository(mock_db)
        messages = await repo.get_messages(conv_id)
        assert len(messages) == 1
        assert messages[0].content == "Hello"
