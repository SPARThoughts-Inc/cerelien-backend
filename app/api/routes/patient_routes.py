from fastapi import APIRouter, Depends, Query

from app.api.deps import get_patient_workflow
from app.domain.workflows.patient_workflow import PatientWorkflow
from app.schemas.patient_schemas import (
    AnalyticsResultResponse,
    GlucoseReadingResponse,
    MedicationResponse,
    PatientListResponse,
    PatientResponse,
    PatientSummaryResponse,
)

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("", response_model=PatientListResponse)
async def list_patients(
    workflow: PatientWorkflow = Depends(get_patient_workflow),
):
    patients = await workflow.list_patients()
    return PatientListResponse(
        patients=[PatientResponse.model_validate(p.model_dump()) for p in patients],
        count=len(patients),
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    workflow: PatientWorkflow = Depends(get_patient_workflow),
):
    patient = await workflow.get_patient(patient_id)
    return PatientResponse.model_validate(patient.model_dump())


@router.get("/{patient_id}/glucose", response_model=list[GlucoseReadingResponse])
async def get_glucose_readings(
    patient_id: int,
    days: int = Query(default=30, ge=1, le=365),
    type: str | None = Query(default=None, alias="type"),
    workflow: PatientWorkflow = Depends(get_patient_workflow),
):
    readings = await workflow.get_glucose_readings(patient_id, days, type)
    return [GlucoseReadingResponse.model_validate(r.model_dump()) for r in readings]


@router.get("/{patient_id}/analytics", response_model=AnalyticsResultResponse | None)
async def get_analytics(
    patient_id: int,
    workflow: PatientWorkflow = Depends(get_patient_workflow),
):
    result = await workflow.get_analytics(patient_id)
    if not result:
        return None
    return AnalyticsResultResponse.model_validate(result.model_dump())


@router.get("/{patient_id}/medications", response_model=list[MedicationResponse])
async def get_medications(
    patient_id: int,
    workflow: PatientWorkflow = Depends(get_patient_workflow),
):
    meds = await workflow.get_medications(patient_id)
    return [MedicationResponse.model_validate(m.model_dump()) for m in meds]


@router.get("/{patient_id}/summary", response_model=PatientSummaryResponse)
async def get_patient_summary(
    patient_id: int,
    workflow: PatientWorkflow = Depends(get_patient_workflow),
):
    summary = await workflow.get_summary(patient_id)
    return PatientSummaryResponse(
        patient=PatientResponse.model_validate(summary["patient"].model_dump()),
        latest_a1c=summary["latest_a1c"],
        avg_glucose_30d=summary["avg_glucose_30d"],
        active_alerts=summary["active_alerts"],
    )
