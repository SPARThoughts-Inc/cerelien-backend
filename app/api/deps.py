# Dependency Injection providers for FastAPI routes.
from app.domain.workflows.patient_workflow import PatientWorkflow
from app.infrastructure.adapters.db.postgres import DatabaseAdapter
from app.infrastructure.repositories.sql_analytics_repository import SQLAnalyticsRepository
from app.infrastructure.repositories.sql_patient_repository import SQLPatientRepository

# Shared DatabaseAdapter instance — initialized via lifespan in main.py
db = DatabaseAdapter()


def get_patient_workflow() -> PatientWorkflow:
    patient_repo = SQLPatientRepository(db)
    analytics_repo = SQLAnalyticsRepository(db)
    return PatientWorkflow(patient_repo=patient_repo, analytics_repo=analytics_repo)
