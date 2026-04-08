from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AnalyticsResult(BaseModel):
    id: UUID
    patient_id: UUID
    result_type: str
    result_data: dict[str, Any]
    generated_at: datetime | None = None
