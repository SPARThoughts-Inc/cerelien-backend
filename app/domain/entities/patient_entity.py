from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Patient(BaseModel):
    id: UUID
    firebase_uid: str
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    diabetes_type: Literal["type1", "type2", "gestational", "prediabetes"] | None = None
    diagnosis_date: date | None = None
    phone_number: str | None = None
    created_at: datetime | None = None
