from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator


class Medication(BaseModel):
    id: UUID
    patient_id: UUID
    name: str
    dosage: str | None = None
    frequency: str | None = None
    adherence_rate: Decimal | None = None

    @field_validator("adherence_rate")
    @classmethod
    def adherence_rate_must_be_in_range(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and (v < 0 or v > 100):
            raise ValueError("adherence_rate must be between 0 and 100")
        return v
