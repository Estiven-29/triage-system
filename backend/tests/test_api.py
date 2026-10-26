import os

# Por defecto SQLite, nueva en cada ejecucion para que los resultados no
# dependan de corridas anteriores. CI define TEST_DATABASE_URL para correr
# los mismos tests contra una BD Postgres vacia.
if "TEST_DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
else:
    if os.path.exists("test_triage.db"):
        os.remove("test_triage.db")
    os.environ["DATABASE_URL"] = "sqlite:///./test_triage.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import SessionLocal  # noqa: E402
from app.db.migrations import run_migrations  # noqa: E402
from app.main import app  # noqa: E402
from app.models.models import MedicalStaff  # noqa: E402

run_migrations()

with SessionLocal() as _db:
    _db.add(
        MedicalStaff(
            employee_id="DOC-TEST",
            full_name="Dra. Prueba",
            role="emergency_physician",
            max_patient_capacity=200,
            is_available=True,
        )
    )
    _db.commit()

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_full_intake_and_classification_flow():
    start = client.post(
        "/api/chatbot/start",
        json={
            "first_name": "Ana",
            "last_name": "Gomez",
            "date_of_birth": "1990-05-10",
            "gender": "female",
        },
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]
    assert session_id

    msg1 = client.post(
        "/api/chatbot/message",
        json={"session_id": session_id, "message": "Tengo fiebre y tos fuerte"},
    )
    assert msg1.status_code == 200
    assert msg1.json()["conversation_complete"] is False

    msg2 = client.post(
        "/api/chatbot/message",
        json={"session_id": session_id, "message": "Desde hace 2 dias"},
    )
    assert msg2.status_code == 200
    assert msg2.json()["conversation_complete"] is True

    classify = client.post(
        "/api/triage/classify",
        json={
            "patient_id": session_id,
            "vital_signs": {
                "heart_rate": 110,
                "respiratory_rate": 22,
                "systolic_bp": 100,
                "diastolic_bp": 65,
                "spo2": 93,
                "temperature": 38.9,
            },
            "chief_complaint": "Tengo fiebre y tos fuerte",
            "symptoms": ["fiebre", "tos"],
        },
    )
    assert classify.status_code == 200
    body = classify.json()
    assert body["classification"] in {"NORMAL", "URGENTE", "CRITICO"}
    assert 0.0 <= body["confidence"] <= 1.0
    assert isinstance(body["safety_override"], bool)
    assert body["tiss28_score"] >= 0
    assert isinstance(body["recommended_actions"], list)
    assert body["assigned_to"] == "Dra. Prueba"

    metrics = client.get("/api/dashboard/metrics")
    assert metrics.status_code == 200
    assert metrics.json()["systemMetrics"]["totalPatients"] >= 1

    active = client.get("/api/dashboard/active-patients")
    assert active.status_code == 200
    names = [p["name"] for p in active.json()]
    assert "Ana Gomez" in names


def test_classify_rejects_invalid_vitals():
    response = client.post(
        "/api/triage/classify",
        json={
            "patient_id": "nonexistent",
            "vital_signs": {
                "heart_rate": -5,
                "respiratory_rate": 16,
                "systolic_bp": 120,
                "diastolic_bp": 80,
                "spo2": 98,
                "temperature": 36.8,
            },
            "chief_complaint": "test",
            "symptoms": [],
        },
    )
    assert response.status_code == 422


VALID_VITALS = {
    "heart_rate": 80,
    "respiratory_rate": 16,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "spo2": 98,
    "temperature": 36.8,
}


def test_classify_unknown_patient_returns_404():
    response = client.post(
        "/api/triage/classify",
        json={"patient_id": "no-existe", "vital_signs": VALID_VITALS, "symptoms": []},
    )
    assert response.status_code == 404
    assert "Paciente no encontrado" in response.json()["detail"]


def test_message_to_unknown_session_returns_404():
    response = client.post(
        "/api/chatbot/message", json={"session_id": "no-existe", "message": "hola"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Sesion de chatbot no encontrada: no-existe"


def _new_classified_patient() -> tuple[str, int]:
    start = client.post("/api/chatbot/start", json={"first_name": "Luis", "last_name": "Alta"})
    patient_id = start.json()["session_id"]
    classify = client.post(
        "/api/triage/classify",
        json={"patient_id": patient_id, "vital_signs": VALID_VITALS, "symptoms": []},
    )
    assert classify.status_code == 200
    active = client.get("/api/dashboard/active-patients").json()
    (entry,) = [p for p in active if p["name"] == "Luis Alta"]
    return patient_id, int(entry["id"])


def _staff_load(name: str) -> dict:
    (entry,) = [s for s in client.get("/api/dashboard/staff-workload").json() if s["name"] == name]
    return entry


def test_discharge_removes_patient_from_active_list_and_frees_staff_load():
    _, assessment_id = _new_classified_patient()
    load_before = _staff_load("Dra. Prueba")

    response = client.post(f"/api/triage/assessments/{assessment_id}/discharge")
    assert response.status_code == 200
    assert response.json()["id"] == assessment_id

    active_ids = [int(p["id"]) for p in client.get("/api/dashboard/active-patients").json()]
    assert assessment_id not in active_ids
    assert _staff_load("Dra. Prueba")["patients"] == load_before["patients"] - 1

    again = client.post(f"/api/triage/assessments/{assessment_id}/discharge")
    assert again.status_code == 409


def test_discharge_unknown_assessment_returns_404():
    assert client.post("/api/triage/assessments/999999/discharge").status_code == 404
