import logging
from uuid import UUID

from app.core.exceptions import InfrastructureError
from app.domain.entities.analytics_result_entity import AnalyticsResult
from app.domain.interfaces.analytics_repository import AnalyticsRepository
from app.infrastructure.adapters.db.postgres import DatabaseAdapter
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class SQLAnalyticsRepository(AnalyticsRepository):
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    async def get_by_patient(self, patient_id: UUID) -> list[AnalyticsResult]:
        rows = await self.db.fetch_all(
            "SELECT * FROM analytics_results WHERE patient_id = $1 ORDER BY generated_at DESC",
            patient_id,
        )
        try:
            return [AnalyticsResult.model_validate(row) for row in rows]
        except ValidationError as e:
            logger.error("DB data validation failed for analytics results: %s", e)
            raise InfrastructureError("Invalid data shape in database")

    async def get_by_type(self, patient_id: UUID, result_type: str) -> list[AnalyticsResult]:
        rows = await self.db.fetch_all(
            "SELECT * FROM analytics_results WHERE patient_id = $1 AND result_type = $2 ORDER BY generated_at DESC",
            patient_id,
            result_type,
        )
        try:
            return [AnalyticsResult.model_validate(row) for row in rows]
        except ValidationError as e:
            logger.error("DB data validation failed for analytics results by type: %s", e)
            raise InfrastructureError("Invalid data shape in database")
