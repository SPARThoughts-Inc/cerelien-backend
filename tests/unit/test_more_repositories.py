"""Additional repository tests for coverage."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import InfrastructureError
from app.infrastructure.repositories.sql_conversation_repository import SQLConversationRepository
from app.infrastructure.repositories.sql_patient_repository import SQLPatientRepository


@pytest.fixture
def mock_db():
    return AsyncMock()


class TestSQLPatientRepositoryAdditional:
    @pytest.mark.asyncio
    async def test_get_by_firebase_uid_found(self, mock_db):
        patient_id = uuid4()
        mock_db.fetch_one.return_value = {
            "id": patient_id, "firebase_uid": "firebase_abc",
            "first_name": "Jane", "last_name": "Doe",
            "date_of_birth": None, "diabetes_type": "type1",
            "diagnosis_date": None, "phone_number": "+15551234567",
            "created_at": datetime.now(),
        }
        repo = SQLPatientRepository(mock_db)
        result = await repo.get_by_firebase_uid("firebase_abc")
        assert result is not None
        assert result.firebase_uid == "firebase_abc"

    @pytest.mark.asyncio
    async def test_get_by_firebase_uid_not_found(self, mock_db):
        mock_db.fetch_one.return_value = None
        repo = SQLPatientRepository(mock_db)
        result = await repo.get_by_firebase_uid("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_phone_found(self, mock_db):
        patient_id = uuid4()
        mock_db.fetch_one.return_value = {
            "id": patient_id, "firebase_uid": "uid1",
            "first_name": "Bob", "last_name": "Smith",
            "date_of_birth": None, "diabetes_type": None,
            "diagnosis_date": None, "phone_number": "+15559876543",
            "created_at": None,
        }
        repo = SQLPatientRepository(mock_db)
        result = await repo.get_by_phone("+15559876543")
        assert result is not None
        assert result.phone_number == "+15559876543"

    @pytest.mark.asyncio
    async def test_get_by_phone_not_found(self, mock_db):
        mock_db.fetch_one.return_value = None
        repo = SQLPatientRepository(mock_db)
        result = await repo.get_by_phone("+10000000000")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_glucose_readings_with_type(self, mock_db):
        patient_id = uuid4()
        mock_db.fetch_all.return_value = [
            {
                "id": uuid4(), "patient_id": patient_id,
                "reading_value": Decimal("7.5"), "reading_type": "a1c",
                "unit": "%", "recorded_at": datetime.now(), "created_at": None,
            },
        ]
        repo = SQLPatientRepository(mock_db)
        readings = await repo.get_glucose_readings(patient_id, days=365, reading_type="a1c")
        assert len(readings) == 1
        assert readings[0].reading_type == "a1c"


class TestSQLConversationRepositoryAdditional:
    @pytest.mark.asyncio
    async def test_create(self, mock_db):
        conv_id = uuid4()
        patient_id = uuid4()
        now = datetime.now()
        mock_db.fetch_one.return_value = {
            "id": conv_id, "patient_id": patient_id,
            "channel": "web_chat", "started_at": now, "ended_at": None,
        }
        from app.domain.entities.conversation_entity import Conversation
        repo = SQLConversationRepository(mock_db)
        conv = Conversation(id=conv_id, patient_id=patient_id, channel="web_chat")
        result = await repo.create(conv)
        assert result.id == conv_id

    @pytest.mark.asyncio
    async def test_create_fails(self, mock_db):
        mock_db.fetch_one.return_value = None
        from app.domain.entities.conversation_entity import Conversation
        repo = SQLConversationRepository(mock_db)
        conv = Conversation(id=uuid4(), patient_id=uuid4(), channel="web_chat")
        with pytest.raises(InfrastructureError):
            await repo.create(conv)

    @pytest.mark.asyncio
    async def test_add_message(self, mock_db):
        msg_id = uuid4()
        conv_id = uuid4()
        now = datetime.now()
        mock_db.fetch_one.return_value = {
            "id": msg_id, "conversation_id": conv_id,
            "role": "user", "agent_name": None,
            "content": "Hello", "created_at": now,
        }
        from app.domain.entities.message_entity import Message
        repo = SQLConversationRepository(mock_db)
        msg = Message(id=msg_id, conversation_id=conv_id, role="user", content="Hello")
        result = await repo.add_message(msg)
        assert result.id == msg_id

    @pytest.mark.asyncio
    async def test_add_message_fails(self, mock_db):
        mock_db.fetch_one.return_value = None
        from app.domain.entities.message_entity import Message
        repo = SQLConversationRepository(mock_db)
        msg = Message(id=uuid4(), conversation_id=uuid4(), role="user", content="Hi")
        with pytest.raises(InfrastructureError):
            await repo.add_message(msg)

    @pytest.mark.asyncio
    async def test_get_patient_conversations(self, mock_db):
        patient_id = uuid4()
        conv_id = uuid4()
        now = datetime.now()
        mock_db.fetch_all.return_value = [
            {
                "id": conv_id, "patient_id": patient_id,
                "channel": "sms", "started_at": now, "ended_at": None,
            },
        ]
        repo = SQLConversationRepository(mock_db)
        result = await repo.get_patient_conversations(patient_id)
        assert len(result) == 1
        assert result[0].channel == "sms"
