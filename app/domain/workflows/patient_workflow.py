from decimal import Decimal

from app.core.exceptions import NotFoundException
from app.domain.entities.analytics_result_entity import AnalyticsResult
from app.domain.entities.glucose_reading_entity import GlucoseReading
from app.domain.entities.medication_entity import Medication
from app.domain.entities.patient_entity import Patient
from app.domain.interfaces.analytics_repository import AnalyticsRepository
from app.domain.interfaces.patient_repository import PatientRepository


class PatientWorkflow:
    def __init__(self, patient_repo: PatientRepository, analytics_repo: AnalyticsRepository):
        self.patient_repo = patient_repo
        self.analytics_repo = analytics_repo

    async def get_patient(self, patient_id: int) -> Patient:
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundException(f"Patient {patient_id} not found")
        return patient

    async def list_patients(self) -> list[Patient]:
        return await self.patient_repo.list_all()

    async def get_glucose_readings(
        self, patient_id: int, days: int = 30, reading_type: str | None = None
    ) -> list[GlucoseReading]:
        # Verify patient exists
        await self.get_patient(patient_id)
        return await self.patient_repo.get_glucose_readings(patient_id, days, reading_type)

    async def get_analytics(self, patient_id: int) -> AnalyticsResult | None:
        await self.get_patient(patient_id)
        return await self.analytics_repo.get_by_patient(patient_id)

    async def get_medications(self, patient_id: int) -> list[Medication]:
        await self.get_patient(patient_id)
        return await self.patient_repo.get_medications(patient_id)

    async def get_summary(self, patient_id: int) -> dict:
        patient = await self.get_patient(patient_id)

        # Get glucose readings for the last 30 days (CGM type for avg calculation)
        cgm_readings = await self.patient_repo.get_glucose_readings(patient_id, days=30, reading_type="cgm")

        # Get latest A1C reading
        a1c_readings = await self.patient_repo.get_glucose_readings(patient_id, days=365, reading_type="a1c")

        # Compute latest A1C
        latest_a1c: Decimal | None = None
        if a1c_readings:
            latest_a1c = a1c_readings[0].value  # Already ordered DESC by reading_timestamp

        # Compute average CGM glucose over 30 days
        avg_glucose_30d: Decimal | None = None
        if cgm_readings:
            total = sum(r.value for r in cgm_readings)
            avg_glucose_30d = total / len(cgm_readings)

        # Active alerts based on complication flags
        active_alerts: list[str] = []
        if latest_a1c is not None and latest_a1c > Decimal("9.0"):
            active_alerts.append("A1C critically high (>9.0%)")
        if avg_glucose_30d is not None and avg_glucose_30d > Decimal("250"):
            active_alerts.append("Average glucose elevated (>250 mg/dL)")
        if avg_glucose_30d is not None and avg_glucose_30d < Decimal("70"):
            active_alerts.append("Average glucose low (<70 mg/dL) - hypoglycemia risk")

        return {
            "patient": patient,
            "latest_a1c": latest_a1c,
            "avg_glucose_30d": avg_glucose_30d,
            "active_alerts": active_alerts,
        }
