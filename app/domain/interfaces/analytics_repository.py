from abc import ABC, abstractmethod

from app.domain.entities.analytics_result_entity import AnalyticsResult


class AnalyticsRepository(ABC):
    @abstractmethod
    async def get_by_patient(self, patient_id: int) -> AnalyticsResult | None: ...
