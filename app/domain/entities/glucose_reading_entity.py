from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class GlucoseReading(BaseModel):
    id: UUID
    patient_id: UUID
    reading_value: Decimal
    reading_type: Literal["cgm", "fingerstick", "a1c"]
    unit: str = "mg/dL"
    recorded_at: datetime
    created_at: datetime | None = None
