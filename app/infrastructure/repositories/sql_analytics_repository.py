import logging

from app.core.exceptions import InfrastructureError
from app.domain.entities.analytics_result_entity import AnalyticsResult
from app.domain.interfaces.analytics_repository import AnalyticsRepository
from app.infrastructure.adapters.db.postgres import DatabaseAdapter
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class SQLAnalyticsRepository(AnalyticsRepository):
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    async def get_by_patient(self, patient_id: int) -> AnalyticsResult | None:
        row = await self.db.fetch_one(
            "SELECT * FROM analytics_results WHERE patient_id = $1 ORDER BY computed_at DESC LIMIT 1",
            patient_id,
        )
        if not row:
            return None
        try:
            return AnalyticsResult.model_validate(row)
        except ValidationError as e:
            logger.error("DB data validation failed for analytics results: %s", e)
            raise InfrastructureError("Invalid data shape in database")
