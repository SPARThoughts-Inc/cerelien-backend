import logging

from app.core.exceptions import InfrastructureError
from app.domain.entities.glucose_reading_entity import GlucoseReading
from app.domain.entities.medication_entity import Medication
from app.domain.entities.patient_entity import Patient
from app.domain.interfaces.patient_repository import PatientRepository
from app.infrastructure.adapters.db.postgres import DatabaseAdapter
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class SQLPatientRepository(PatientRepository):
    def __init__(self, db: DatabaseAdapter):
        self.db = db

    async def get_by_id(self, patient_id: int) -> Patient | None:
        row = await self.db.fetch_one("SELECT * FROM patients WHERE id = $1", patient_id)
        if not row:
            return None
        try:
            return Patient.model_validate(row)
        except ValidationError as e:
            logger.error("DB data validation failed for patient %s: %s", patient_id, e)
            raise InfrastructureError("Invalid data shape in database")

    async def get_by_email(self, email: str) -> Patient | None:
        row = await self.db.fetch_one("SELECT * FROM patients WHERE email = $1", email)
        if not row:
            return None
        try:
            return Patient.model_validate(row)
        except ValidationError as e:
            logger.error("DB data validation failed for email %s: %s", email, e)
            raise InfrastructureError("Invalid data shape in database")

    async def get_by_phone(self, phone_number: str) -> Patient | None:
        row = await self.db.fetch_one("SELECT * FROM patients WHERE phone_number = $1", phone_number)
        if not row:
            return None
        try:
            return Patient.model_validate(row)
        except ValidationError as e:
            logger.error("DB data validation failed for phone %s: %s", phone_number, e)
            raise InfrastructureError("Invalid data shape in database")

    async def list_all(self) -> list[Patient]:
        rows = await self.db.fetch_all("SELECT * FROM patients ORDER BY created_at DESC")
        try:
            return [Patient.model_validate(row) for row in rows]
        except ValidationError as e:
            logger.error("DB data validation failed for patient list: %s", e)
            raise InfrastructureError("Invalid data shape in database")

    async def get_glucose_readings(
        self, patient_id: int, days: int = 30, reading_type: str | None = None
    ) -> list[GlucoseReading]:
        if reading_type:
            query = (
                "SELECT * FROM glucose_readings "
                "WHERE patient_id = $1 AND reading_timestamp >= NOW() - make_interval(days => $2) AND reading_type = $3 "
                "ORDER BY reading_timestamp DESC"
            )
            rows = await self.db.fetch_all(query, patient_id, days, reading_type)
        else:
            query = (
                "SELECT * FROM glucose_readings "
                "WHERE patient_id = $1 AND reading_timestamp >= NOW() - make_interval(days => $2) "
                "ORDER BY reading_timestamp DESC"
            )
            rows = await self.db.fetch_all(query, patient_id, days)
        try:
            return [GlucoseReading.model_validate(row) for row in rows]
        except ValidationError as e:
            logger.error("DB data validation failed for glucose readings: %s", e)
            raise InfrastructureError("Invalid data shape in database")

    async def get_medications(self, patient_id: int) -> list[Medication]:
        rows = await self.db.fetch_all(
            "SELECT * FROM medications WHERE patient_id = $1 ORDER BY name", patient_id
        )
        try:
            return [Medication.model_validate(row) for row in rows]
        except ValidationError as e:
            logger.error("DB data validation failed for medications: %s", e)
            raise InfrastructureError("Invalid data shape in database")
