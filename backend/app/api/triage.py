"""Endpoint de clasificacion de triage."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..ml.classifier import classify
from ..models.models import Patient, TriageAssessment
from ..schemas.schemas import TriageClassifyRequest, TriageClassifyResponse
from ..services.complexity import complexity_level, estimate_complexity_index
from ..services.diagnosis_suggester import recommend_actions, suggest_preliminary_diagnoses
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
