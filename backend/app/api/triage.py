"""Endpoint de clasificacion de triage."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..ml.classifier import classify
from ..models.models import Patient, TriageAssessment, utcnow
from ..schemas.schemas import DischargeResponse, TriageClassifyRequest, TriageClassifyResponse
from ..services.complexity import complexity_level, estimate_complexity_index
from ..services.diagnosis_suggester import recommend_actions, suggest_preliminary_diagnoses
from ..services.staff_assignment import pick_staff
from .websocket import manager

router = APIRouter(prefix="/api/triage", tags=["Triage"])

_RISK_BASE = {"CRITICO": 70, "URGENTE": 40, "NORMAL": 10}


def _assess_and_store(payload: TriageClassifyRequest, db: Session) -> TriageClassifyResponse:
    """Inferencia del modelo + escritura en BD. Es trabajo sincrono y
    bloqueante, por eso el endpoint lo ejecuta en el threadpool."""
    patient = db.get(Patient, payload.patient_id)
    if patient is None:
        raise HTTPException(
            status_code=404, detail=f"Paciente no encontrado: {payload.patient_id}"
        )

    vitals = payload.vital_signs.model_dump()
    symptom_count = len(payload.symptoms)

    classification, confidence, safety_override = classify(vitals, symptom_count)

    complexity_index = estimate_complexity_index(vitals, symptom_count)
    level = complexity_level(complexity_index)

    risk_score = min(100, _RISK_BASE[classification] + complexity_index)

    diagnoses = suggest_preliminary_diagnoses(payload.symptoms)
    actions = recommend_actions(classification, vitals)
    if safety_override:
        actions.insert(
            0,
            "Clasificacion elevada a CRITICO por regla de seguridad "
            "(signos vitales con alerta roja)",
        )

    assessment = TriageAssessment(
        patient_id=payload.patient_id,
        patient_name=f"{patient.first_name} {patient.last_name}",
        chief_complaint=payload.chief_complaint,
        symptoms=payload.symptoms,
        vital_signs=vitals,
        classification=classification,
        confidence=confidence,
        risk_score=risk_score,
        complexity_index=complexity_index,
        complexity_level=level,
        preliminary_diagnoses=diagnoses,
        recommended_actions=actions,
        assigned_staff=pick_staff(db, complexity_index),
    )
    db.add(assessment)
    db.commit()

    return TriageClassifyResponse(
        classification=classification,
        confidence=confidence,
        safety_override=safety_override,
        risk_score=risk_score,
        tiss28_score=complexity_index,
        complexity_level=level,
        preliminary_diagnoses=diagnoses,
        recommended_actions=actions,
        assigned_to=assessment.assigned_staff.full_name if assessment.assigned_staff else None,
    )


@router.post("/classify", response_model=TriageClassifyResponse)
async def classify_patient(payload: TriageClassifyRequest, db: Session = Depends(get_db)):
    result = await run_in_threadpool(_assess_and_store, payload, db)

    await manager.broadcast(
        {
            "type": "new_patient",
            "patient_id": payload.patient_id,
            "classification": result.classification,
        }
    )

    return result


def _discharge(assessment_id: int, db: Session) -> DischargeResponse:
    assessment = db.get(TriageAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail=f"Evaluacion no encontrada: {assessment_id}")
    if assessment.discharged_at is not None:
        raise HTTPException(status_code=409, detail="El paciente ya fue dado de alta")
    assessment.discharged_at = utcnow()
    db.commit()
    return DischargeResponse(id=assessment.id, discharged_at=assessment.discharged_at)


@router.post("/assessments/{assessment_id}/discharge", response_model=DischargeResponse)
async def discharge_patient(assessment_id: int, db: Session = Depends(get_db)):
    """Registra el alta: el paciente deja de contar como activo y libera la
    carga del profesional asignado."""
    result = await run_in_threadpool(_discharge, assessment_id, db)
    await manager.broadcast({"type": "patient_discharged", "assessment_id": result.id})
    return result
