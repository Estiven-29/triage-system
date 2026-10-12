"""Endpoints del dashboard: metricas y lista de pacientes activos."""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.models import Patient, TriageAssessment, utcnow
from ..schemas.schemas import ActivePatient, DashboardMetricsResponse, SystemMetrics

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Cuantos de los ultimos casos clasificados se consideran "activos" para
# efectos de este dashboard de demostracion (no hay flujo de alta/egreso).
ACTIVE_WINDOW = 20


def _bucket_index(complexity_index: int) -> int:
    if complexity_index <= 10:
        return 0
    if complexity_index <= 20:
        return 1
    if complexity_index <= 30:
        return 2
    if complexity_index <= 40:
        return 3
    return 4


def _age_from_dob(dob: str | None) -> int | None:
    if not dob:
        return None
    try:
        birth = date.fromisoformat(dob)
    except ValueError:
        return None
    today = date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def _recent_assessments(db: Session) -> list[TriageAssessment]:
    return (
        db.query(TriageAssessment)
        .order_by(TriageAssessment.created_at.desc())
        .limit(ACTIVE_WINDOW)
        .all()
    )


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    assessments = _recent_assessments(db)
    total = len(assessments)

    critical = sum(1 for a in assessments if a.classification == "CRITICO")
    urgent = sum(1 for a in assessments if a.classification == "URGENTE")
    normal = sum(1 for a in assessments if a.classification == "NORMAL")

    now = utcnow()
    if total:
        avg_wait = sum((now - a.created_at).total_seconds() / 60 for a in assessments) / total
        avg_confidence = sum(a.confidence for a in assessments) / total * 100
        avg_complexity = sum(a.complexity_index for a in assessments) / total
    else:
        avg_wait = avg_confidence = avg_complexity = 0.0

    buckets = [
        {"range": "0-10", "count": 0, "complexity": "Baja"},
        {"range": "11-20", "count": 0, "complexity": "Moderada"},
        {"range": "21-30", "count": 0, "complexity": "Alta"},
        {"range": "31-40", "count": 0, "complexity": "Muy Alta"},
        {"range": "41+", "count": 0, "complexity": "Critica"},
    ]
    for a in assessments:
        buckets[_bucket_index(a.complexity_index)]["count"] += 1

    return DashboardMetricsResponse(
        systemMetrics=SystemMetrics(
            totalPatients=total,
            critical=critical,
            urgent=urgent,
            normal=normal,
            avgWaitTime=round(avg_wait, 1),
            mlConfidence=round(avg_confidence, 1),
            avgTiss28=round(avg_complexity, 1),
        ),
        tiss28Distribution=buckets,
    )


@router.get("/active-patients", response_model=list[ActivePatient])
def get_active_patients(db: Session = Depends(get_db)):
    assessments = _recent_assessments(db)
    if not assessments:
        return []

    patient_ids = [a.patient_id for a in assessments]
    patients = {
        p.id: p for p in db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    }

    now = utcnow()
    result = []
    for a in assessments:
        patient = patients.get(a.patient_id)
        result.append(
            ActivePatient(
                id=str(a.id),
                name=a.patient_name or "Paciente",
                age=_age_from_dob(patient.date_of_birth) if patient else None,
                category=a.classification,
                riskScore=a.risk_score,
                tiss28=a.complexity_index,
                waitTime=int((now - a.created_at).total_seconds() // 60),
                assignedTo=a.assigned_to or "Sin asignar",
                complaint=a.chief_complaint or "",
            )
        )
    return result
