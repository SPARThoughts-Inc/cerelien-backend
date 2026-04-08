from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.analytics_result_entity import AnalyticsResult


class AnalyticsRepository(ABC):
    @abstractmethod
    async def get_by_patient(self, patient_id: UUID) -> list[AnalyticsResult]: ...

    @abstractmethod
    async def get_by_type(self, patient_id: UUID, result_type: str) -> list[AnalyticsResult]: ...
