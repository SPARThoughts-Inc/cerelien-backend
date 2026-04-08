# Dependency Injection providers for FastAPI routes.
from app.domain.workflows.consultation_workflow import ConsultationWorkflow
from app.domain.workflows.patient_workflow import PatientWorkflow
from app.domain.workflows.sms_workflow import SMSWorkflow
from app.infrastructure.adapters.db.postgres import DatabaseAdapter
from app.infrastructure.adapters.twilio_adapter import TwilioAdapter
from app.infrastructure.repositories.sql_analytics_repository import SQLAnalyticsRepository
from app.infrastructure.repositories.sql_conversation_repository import SQLConversationRepository
from app.infrastructure.repositories.sql_patient_repository import SQLPatientRepository

# Shared DatabaseAdapter instance — initialized via lifespan in main.py
db = DatabaseAdapter()


def get_patient_workflow() -> PatientWorkflow:
    patient_repo = SQLPatientRepository(db)
    analytics_repo = SQLAnalyticsRepository(db)
    return PatientWorkflow(patient_repo=patient_repo, analytics_repo=analytics_repo)


def get_consultation_workflow() -> ConsultationWorkflow:
    patient_repo = SQLPatientRepository(db)
    analytics_repo = SQLAnalyticsRepository(db)
    conversation_repo = SQLConversationRepository(db)
    patient_workflow = PatientWorkflow(patient_repo=patient_repo, analytics_repo=analytics_repo)
    return ConsultationWorkflow(
        conversation_repo=conversation_repo,
        patient_workflow=patient_workflow,
    )


def get_twilio_adapter() -> TwilioAdapter:
    return TwilioAdapter()


def get_sms_workflow() -> SMSWorkflow:
    patient_repo = SQLPatientRepository(db)
    analytics_repo = SQLAnalyticsRepository(db)
    conversation_repo = SQLConversationRepository(db)
    patient_workflow = PatientWorkflow(patient_repo=patient_repo, analytics_repo=analytics_repo)
    consultation_workflow = ConsultationWorkflow(
        conversation_repo=conversation_repo,
        patient_workflow=patient_workflow,
    )
    twilio = TwilioAdapter()
    return SMSWorkflow(
        patient_repo=patient_repo,
        consultation_workflow=consultation_workflow,
        conversation_repo=conversation_repo,
        twilio=twilio,
    )
