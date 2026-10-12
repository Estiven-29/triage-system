from datetime import timedelta

import pytest

from app.models.models import ChatSession, Patient, utcnow
from app.services.chatbot_service import ChatbotService, ChatSessionNotFound, extract_symptoms


def _start(service, db, first="Juan", last="Perez"):
    patient = Patient(first_name=first, last_name=last)
    db.add(patient)
    db.flush()
    greeting = service.start_session(db, patient)
    db.commit()
    return patient.id, greeting


def test_extract_symptoms_matches_keywords():
    symptoms = extract_symptoms("Tengo fiebre y mucha tos desde ayer")
    assert "fiebre" in symptoms
    assert "tos" in symptoms


def test_extract_symptoms_ignores_accents_case():
    symptoms = extract_symptoms("DOLOR DE CABEZA Y NAUSEA")
    assert "cefalea" in symptoms
    assert "nauseas" in symptoms


def test_chatbot_flow_completes_in_two_turns(db):
    service = ChatbotService()
    session_id, greeting = _start(service, db)
    assert "Juan Perez" in greeting

    first = service.handle_message(db, session_id, "Tengo dolor en el pecho y falta de aire")
    assert first["conversation_complete"] is False
    assert "dolor toracico" in first["extracted_data"]["symptoms"]

    second = service.handle_message(db, session_id, "Hace 2 horas, dolor 8 de 10")
    assert second["conversation_complete"] is True


def test_session_survives_a_new_service_instance(db):
    # Simula un reinicio del backend: el estado vive en BD, no en memoria.
    session_id, _ = _start(ChatbotService(), db)
    ChatbotService().handle_message(db, session_id, "Tengo fiebre")

    second = ChatbotService().handle_message(db, session_id, "Desde ayer")
    assert second["conversation_complete"] is True
    assert second["extracted_data"]["chief_complaint"] == "Tengo fiebre"


def test_unknown_session_raises(db):
    service = ChatbotService()
    with pytest.raises(ChatSessionNotFound):
        service.handle_message(db, "no-existe", "hola")


def test_expired_session_raises_and_is_deleted(db):
    service = ChatbotService(ttl_minutes=30)
    session_id, _ = _start(service, db)
    db.get(ChatSession, session_id).updated_at = utcnow() - timedelta(minutes=31)
    db.commit()

    with pytest.raises(ChatSessionNotFound, match="expiro"):
        service.handle_message(db, session_id, "hola")
    assert db.get(ChatSession, session_id) is None


def test_starting_a_session_purges_expired_ones(db):
    service = ChatbotService(ttl_minutes=30)
    old_id, _ = _start(service, db, "Viejo", "Paciente")
    db.get(ChatSession, old_id).updated_at = utcnow() - timedelta(hours=1)
    db.commit()

    new_id, _ = _start(service, db, "Nuevo", "Paciente")
    assert db.get(ChatSession, old_id) is None
    assert db.get(ChatSession, new_id) is not None
