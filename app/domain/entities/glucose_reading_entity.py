from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class GlucoseReading(BaseModel):
    id: int
    patient_id: int
    reading_timestamp: datetime
    reading_type: Literal["cgm", "a1c"]
    value: Decimal
    unit: str = "mg/dL"
    created_at: datetime | None = None
