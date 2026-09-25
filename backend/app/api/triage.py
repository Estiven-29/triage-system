"""Endpoint de clasificacion de triage."""
from fastapi import APIRouter, Depends
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


@router.post("/classify", response_model=TriageClassifyResponse)
async def classify_patient(payload: TriageClassifyRequest, db: Session = Depends(get_db)):
    vitals = payload.vital_signs.model_dump()
    symptom_count = len(payload.symptoms)

    classification, confidence = classify(vitals, symptom_count)

    complexity_index = estimate_complexity_index(vitals, symptom_count)
    level = complexity_level(complexity_index)

    risk_score = min(100, _RISK_BASE[classification] + complexity_index)

    diagnoses = suggest_preliminary_diagnoses(payload.symptoms)
    actions = recommend_actions(classification, vitals)

    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    patient_name = f"{patient.first_name} {patient.last_name}" if patient else "Paciente"

    assessment = TriageAssessment(
        patient_id=payload.patient_id,
        patient_name=patient_name,
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

    await manager.broadcast(
        {
            "type": "new_patient",
            "patient_id": payload.patient_id,
            "classification": classification,
        }
    )

    return TriageClassifyResponse(
        classification=classification,
        confidence=confidence,
        risk_score=risk_score,
        tiss28_score=complexity_index,
        complexity_level=level,
        preliminary_diagnoses=diagnoses,
        recommended_actions=actions,
    )
