from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class Patient(BaseModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    diabetes_type: Literal["type_1", "type_2", "gestational", "prediabetes"] | None = None
    phone_number: str | None = None
    email: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
