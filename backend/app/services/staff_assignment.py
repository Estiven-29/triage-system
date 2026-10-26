"""
Asignacion automatica de personal y calculo de carga de trabajo.

La carga de un profesional es la suma del indice de complejidad de sus
pacientes activos (sin alta), en la misma escala que max_patient_capacity.
Cada paciente nuevo se asigna al profesional disponible con menor carga
relativa que todavia tenga capacidad para absorberlo; si nadie la tiene,
queda sin asignar para que se resuelva manualmente.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.models import MedicalStaff, TriageAssessment


@dataclass
class StaffLoad:
    staff: MedicalStaff
    load: int
    patients: int

    @property
    def capacity(self) -> int:
        return self.staff.max_patient_capacity or 0

    def has_room_for(self, complexity_index: int) -> bool:
        return self.load + complexity_index <= self.capacity

    @property
    def load_ratio(self) -> float:
        return self.load / self.capacity if self.capacity else float("inf")


def staff_loads(db: Session) -> list[StaffLoad]:
    """Carga actual de todo el personal, incluido el no disponible."""
    rows = (
        db.query(
            TriageAssessment.assigned_staff_id,
            func.coalesce(func.sum(TriageAssessment.complexity_index), 0),
            func.count(TriageAssessment.id),
        )
        .filter(
            TriageAssessment.discharged_at.is_(None),
            TriageAssessment.assigned_staff_id.is_not(None),
        )
        .group_by(TriageAssessment.assigned_staff_id)
        .all()
    )
    by_staff = {staff_id: (int(load), count) for staff_id, load, count in rows}
    return [
        StaffLoad(staff, *by_staff.get(staff.id, (0, 0)))
        for staff in db.query(MedicalStaff).order_by(MedicalStaff.id).all()
    ]


def pick_staff(db: Session, complexity_index: int) -> MedicalStaff | None:
    candidates = [
        entry
        for entry in staff_loads(db)
        if entry.staff.is_available and entry.has_room_for(complexity_index)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda entry: (entry.load_ratio, entry.staff.id)).staff
