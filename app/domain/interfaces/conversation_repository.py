from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.conversation_entity import Conversation
from app.domain.entities.message_entity import Message


class ConversationRepository(ABC):
    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Conversation | None: ...

    @abstractmethod
    async def add_message(self, message: Message) -> Message: ...

    @abstractmethod
    async def get_messages(self, conversation_id: UUID) -> list[Message]: ...

    @abstractmethod
    async def get_patient_conversations(self, patient_id: UUID) -> list[Conversation]: ...
