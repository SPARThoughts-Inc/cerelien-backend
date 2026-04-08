from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class Medication(BaseModel):
    id: int
    patient_id: int
    name: str
    dosage: str | None = None
    frequency: str | None = None
    adherence_rate: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime | None = None

    @field_validator("adherence_rate")
    @classmethod
    def adherence_rate_must_be_in_range(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and (v < 0 or v > 1):
            raise ValueError("adherence_rate must be between 0.00 and 1.00")
        return v
