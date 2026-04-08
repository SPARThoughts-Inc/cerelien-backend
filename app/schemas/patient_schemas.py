from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel


class PatientResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    diabetes_type: Literal["type_1", "type_2", "gestational", "prediabetes"] | None = None
    phone_number: str | None = None
    email: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class GlucoseReadingResponse(BaseModel):
    id: int
    patient_id: int
    reading_timestamp: datetime
    reading_type: Literal["cgm", "a1c"]
    value: Decimal
    unit: str
    created_at: datetime | None = None


class AnalyticsResultResponse(BaseModel):
    id: int
    patient_id: int
    risk_score: dict[str, Any] | None = None
    trend: dict[str, Any] | None = None
    complication_flags: list[Any] | None = None
    computed_at: datetime | None = None


class MedicationResponse(BaseModel):
    id: int
    patient_id: int
    name: str
    dosage: str | None = None
    frequency: str | None = None
    adherence_rate: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime | None = None


class PatientSummaryResponse(BaseModel):
    patient: PatientResponse
    latest_a1c: Decimal | None = None
    avg_glucose_30d: Decimal | None = None
    active_alerts: list[str] = []


class PatientListResponse(BaseModel):
    patients: list[PatientResponse]
    count: int
