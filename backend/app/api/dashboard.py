"""Endpoints del dashboard: metricas y lista de pacientes activos."""
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from ..db.database import get_db
from ..models.models import Patient, TriageAssessment, utcnow
from ..schemas.schemas import (
    ActivePatient,
    DashboardMetricsResponse,
    StaffWorkload,
    SystemMetrics,
)
from ..services.complexity import COMPLEXITY_LEVELS, complexity_level_index
from ..services.staff_assignment import staff_loads

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Tope de seguridad para no devolver listas enormes si nadie da altas.
MAX_ACTIVE_PATIENTS = 200


def _age_from_dob(dob: str | None) -> int | None:
    if not dob:
        return None
    try:
        birth = date.fromisoformat(dob)
    except ValueError:
        return None
    today = date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def _active_assessments(db: Session) -> list[TriageAssessment]:
    """Pacientes activos: clasificados y todavia sin alta."""
    return (
        db.query(TriageAssessment)
        .options(joinedload(TriageAssessment.assigned_staff))
        .filter(TriageAssessment.discharged_at.is_(None))
        .order_by(TriageAssessment.created_at.desc())
        .limit(MAX_ACTIVE_PATIENTS)
        .all()
    )


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    assessments = _active_assessments(db)
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
        {"range": label, "count": 0, "complexity": name}
        for _upper, name, label in COMPLEXITY_LEVELS
    ]
    for a in assessments:
        buckets[complexity_level_index(a.complexity_index)]["count"] += 1

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
    assessments = _active_assessments(db)
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
                assignedTo=a.assigned_staff.full_name if a.assigned_staff else "Sin asignar",
                complaint=a.chief_complaint or "",
            )
        )
    return result


@router.get("/staff-workload", response_model=list[StaffWorkload])
def get_staff_workload(db: Session = Depends(get_db)):
    return [
        StaffWorkload(
            id=entry.staff.id,
            name=entry.staff.full_name,
            role=entry.staff.specialization or entry.staff.role,
            tiss28Load=entry.load,
            capacity=entry.capacity,
            patients=entry.patients,
            available=bool(entry.staff.is_available),
        )
        for entry in staff_loads(db)
    ]
