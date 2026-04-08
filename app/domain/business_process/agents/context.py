from dataclasses import dataclass

from app.domain.workflows.patient_workflow import PatientWorkflow


@dataclass
class ConsultationContext:
    patient_id: str
    patient_workflow: PatientWorkflow
    channel: str = "web"
