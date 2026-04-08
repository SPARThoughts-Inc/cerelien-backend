import logging

from app.core.exceptions import InfrastructureError
from app.domain.entities.conversation_entity import Conversation
from app.domain.entities.message_entity import Message
from app.domain.interfaces.conversation_repository import ConversationRepository
from app.infrastructure.adapters.db.postgres import DatabaseAdapter
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class SQLConversationRepository(ConversationRepository):
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    async def create(self, conversation: Conversation) -> Conversation:
        row = await self.db.fetch_one(
            "INSERT INTO conversations (patient_id, channel, status) "
            "VALUES ($1, $2, $3) RETURNING *",
            conversation.patient_id,
            conversation.channel,
            conversation.status or "active",
        )
        if not row:
            raise InfrastructureError("Failed to create conversation")
        try:
            return Conversation.model_validate(row)
        except ValidationError as e:
            logger.error("DB data validation failed for conversation create: %s", e)
            raise InfrastructureError("Invalid data shape in database")

    async def get_by_id(self, conversation_id: int) -> Conversation | None:
        row = await self.db.fetch_one(
            "SELECT * FROM conversations WHERE id = $1", conversation_id
        )
        if not row:
            return None
        try:
            return Conversation.model_validate(row)
        except ValidationError as e:
            logger.error("DB data validation failed for conversation %s: %s", conversation_id, e)
            raise InfrastructureError("Invalid data shape in database")

    async def add_message(self, message: Message) -> Message:
        row = await self.db.fetch_one(
            "INSERT INTO messages (conversation_id, role, content) "
            "VALUES ($1, $2, $3) RETURNING *",
            message.conversation_id,
            message.role,
            message.content,
        )
        if not row:
            raise InfrastructureError("Failed to add message")
        try:
            return Message.model_validate(row)
        except ValidationError as e:
            logger.error("DB data validation failed for message create: %s", e)
            raise InfrastructureError("Invalid data shape in database")

    async def get_messages(self, conversation_id: int) -> list[Message]:
        rows = await self.db.fetch_all(
            "SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at ASC",
            conversation_id,
        )
        try:
            return [Message.model_validate(row) for row in rows]
        except ValidationError as e:
            logger.error("DB data validation failed for messages: %s", e)
            raise InfrastructureError("Invalid data shape in database")

    async def get_patient_conversations(self, patient_id: int) -> list[Conversation]:
        rows = await self.db.fetch_all(
            "SELECT * FROM conversations WHERE patient_id = $1 ORDER BY started_at DESC",
            patient_id,
        )
        try:
            return [Conversation.model_validate(row) for row in rows]
        except ValidationError as e:
            logger.error("DB data validation failed for patient conversations: %s", e)
            raise InfrastructureError("Invalid data shape in database")
