from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class PatientResponse(BaseModel):
    id: UUID
    firebase_uid: str
    first_name: str
    last_name: str
    date_of_birth: date | None = None
    diabetes_type: Literal["type1", "type2", "gestational", "prediabetes"] | None = None
    diagnosis_date: date | None = None
    phone_number: str | None = None
    created_at: datetime | None = None


class GlucoseReadingResponse(BaseModel):
    id: UUID
    patient_id: UUID
    reading_value: Decimal
    reading_type: Literal["cgm", "fingerstick", "a1c"]
    unit: str
    recorded_at: datetime
    created_at: datetime | None = None


class AnalyticsResultResponse(BaseModel):
    id: UUID
    patient_id: UUID
    result_type: str
    result_data: dict[str, Any]
    generated_at: datetime | None = None


class MedicationResponse(BaseModel):
    id: UUID
    patient_id: UUID
    name: str
    dosage: str | None = None
    frequency: str | None = None
    adherence_rate: Decimal | None = None


class PatientSummaryResponse(BaseModel):
    patient: PatientResponse
    latest_a1c: Decimal | None = None
    avg_glucose_30d: Decimal | None = None
    active_alerts: list[str] = []


class PatientListResponse(BaseModel):
    patients: list[PatientResponse]
    count: int
