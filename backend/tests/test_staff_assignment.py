from app.models.models import MedicalStaff, Patient, TriageAssessment, utcnow
from app.services.staff_assignment import pick_staff, staff_loads


def _staff(db, employee_id, capacity, available=True):
    staff = MedicalStaff(
        employee_id=employee_id,
        full_name=f"Dr. {employee_id}",
        role="emergency_physician",
        max_patient_capacity=capacity,
        is_available=available,
    )
    db.add(staff)
    db.flush()
    return staff


def _assessment(db, staff, complexity, discharged=False):
    patient = Patient(first_name="P", last_name=str(complexity))
    db.add(patient)
    db.flush()
    db.add(
        TriageAssessment(
            patient_id=patient.id,
            classification="URGENTE",
            confidence=0.9,
            risk_score=50,
            complexity_index=complexity,
            complexity_level="Moderada",
            assigned_staff=staff,
            discharged_at=utcnow() if discharged else None,
        )
    )
    db.flush()


def test_picks_least_loaded_relative_to_capacity(db):
    busy = _staff(db, "A", capacity=50)
    free = _staff(db, "B", capacity=50)
    _assessment(db, busy, 30)
    _assessment(db, free, 10)
    assert pick_staff(db, 5) == free


def test_skips_unavailable_and_full_staff(db):
    _staff(db, "OFF", capacity=100, available=False)
    full = _staff(db, "FULL", capacity=20)
    _assessment(db, full, 18)
    assert pick_staff(db, 5) is None


def test_discharged_patients_do_not_count_as_load(db):
    staff = _staff(db, "A", capacity=20)
    _assessment(db, staff, 18, discharged=True)
    assert pick_staff(db, 15) == staff
    (entry,) = staff_loads(db)
    assert (entry.load, entry.patients) == (0, 0)


def test_staff_loads_include_staff_without_patients(db):
    a = _staff(db, "A", capacity=50)
    _staff(db, "B", capacity=40)
    _assessment(db, a, 12)
    _assessment(db, a, 8)
    loads = {entry.staff.employee_id: (entry.load, entry.patients) for entry in staff_loads(db)}
    assert loads == {"A": (20, 2), "B": (0, 0)}
