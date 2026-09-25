import pytest

from app.services.chatbot_service import ChatbotService, extract_symptoms


def test_extract_symptoms_matches_keywords():
    symptoms = extract_symptoms("Tengo fiebre y mucha tos desde ayer")
    assert "fiebre" in symptoms
    assert "tos" in symptoms


def test_extract_symptoms_ignores_accents_case():
    symptoms = extract_symptoms("DOLOR DE CABEZA Y NAUSEA")
    assert "cefalea" in symptoms
    assert "nauseas" in symptoms


def test_chatbot_flow_completes_in_two_turns():
    service = ChatbotService()
    session_id, greeting = service.start_session("Juan Perez")
    assert greeting

    first = service.handle_message(session_id, "Tengo dolor en el pecho y falta de aire")
    assert first["conversation_complete"] is False
    assert "dolor toracico" in first["extracted_data"]["symptoms"]

    second = service.handle_message(session_id, "Hace 2 horas, dolor 8 de 10")
    assert second["conversation_complete"] is True


def test_unknown_session_raises():
    service = ChatbotService()
    with pytest.raises(KeyError):
        service.handle_message("no-existe", "hola")
