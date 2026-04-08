from abc import ABC, abstractmethod

from app.domain.entities.glucose_reading_entity import GlucoseReading
from app.domain.entities.medication_entity import Medication
from app.domain.entities.patient_entity import Patient


class PatientRepository(ABC):
    @abstractmethod
    async def get_by_id(self, patient_id: int) -> Patient | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Patient | None: ...

    @abstractmethod
    async def get_by_phone(self, phone_number: str) -> Patient | None: ...

    @abstractmethod
    async def list_all(self) -> list[Patient]: ...

    @abstractmethod
    async def get_glucose_readings(
        self, patient_id: int, days: int = 30, reading_type: str | None = None
    ) -> list[GlucoseReading]: ...

    @abstractmethod
    async def get_medications(self, patient_id: int) -> list[Medication]: ...
