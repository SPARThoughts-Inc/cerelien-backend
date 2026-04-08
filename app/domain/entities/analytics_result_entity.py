from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AnalyticsResult(BaseModel):
    id: int
    patient_id: int
    risk_score: dict[str, Any] | None = None
    trend: dict[str, Any] | None = None
    complication_flags: list[Any] | None = None
    computed_at: datetime | None = None
