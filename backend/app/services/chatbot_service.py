"""
Chatbot de intake conversacional.

Es un asistente basado en reglas (deteccion de sintomas por palabras clave +
maquina de estados de 2 turnos), no un modelo de lenguaje generativo. Se
documenta explicitamente para no sobre-representar la solucion como "IA
generativa" cuando en realidad es un flujo guiado con extraccion de
palabras clave.
"""
from __future__ import annotations

import unicodedata
import uuid

SYMPTOM_KEYWORDS: dict[str, str] = {
    "dolor de cabeza": "cefalea",
    "cefalea": "cefalea",
    "fiebre": "fiebre",
    "tos": "tos",
    "dificultad para respirar": "dificultad respiratoria",
    "falta de aire": "dificultad respiratoria",
    "ahogo": "dificultad respiratoria",
    "dolor en el pecho": "dolor toracico",
    "dolor toracico": "dolor toracico",
    "dolor de pecho": "dolor toracico",
    "nausea": "nauseas",
    "vomito": "vomitos",
    "mareo": "mareo",
    "mareado": "mareo",
    "dolor abdominal": "dolor abdominal",
    "dolor de estomago": "dolor abdominal",
    "sangrado": "sangrado",
    "sangre": "sangrado",
    "debilidad": "debilidad",
    "cansancio": "fatiga",
    "fatiga": "fatiga",
    "dolor muscular": "dolor muscular",
    "diarrea": "diarrea",
    "convulsion": "convulsiones",
    "desmayo": "perdida de conciencia",
    "perdida de conciencia": "perdida de conciencia",
    "hinchazon": "edema",
    "erupcion": "erupcion cutanea",
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return text


def extract_symptoms(*texts: str) -> list[str]:
    combined = _normalize(" ".join(texts))
    found: list[str] = []
    for keyword, canonical in SYMPTOM_KEYWORDS.items():
        if _normalize(keyword) in combined and canonical not in found:
            found.append(canonical)
    return found


class ChatbotSession:
    def __init__(self, patient_name: str):
        self.patient_name = patient_name
        self.turn = 0
        self.chief_complaint = ""
        self.symptoms: list[str] = []


class ChatbotService:
    """Sesiones en memoria. Para produccion real se recomienda Redis u otro
    almacen compartido si el backend corre con multiples workers."""

    def __init__(self):
        self._sessions: dict[str, ChatbotSession] = {}

    def start_session(self, patient_name: str) -> tuple[str, str]:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = ChatbotSession(patient_name)
        greeting = (
            f"Hola {patient_name}, soy el asistente de admision. "
            "Cuentame en tus palabras: ¿cual es el motivo principal de tu "
            "consulta y que sintomas presentas?"
        )
        return session_id, greeting

    def handle_message(self, session_id: str, message: str) -> dict:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Sesion de chatbot no encontrada: {session_id}")

        session.turn += 1

        if session.turn == 1:
            session.chief_complaint = message.strip()
            session.symptoms = extract_symptoms(message)
            response = (
                "Entiendo. ¿Desde hace cuanto tiempo tienes estos sintomas "
                "y en una escala del 1 al 10, que tan intensos son?"
            )
            return {
                "response": response,
                "extracted_data": {
                    "chief_complaint": session.chief_complaint,
                    "symptoms": session.symptoms,
                },
                "conversation_complete": False,
            }

        # Turno 2: cerramos la conversacion y volvemos a extraer por si
        # el paciente menciono sintomas nuevos en este mensaje.
        session.symptoms = extract_symptoms(session.chief_complaint, message)
        response = (
            "Gracias por la informacion. Ahora vamos a registrar tus signos "
            "vitales para completar la clasificacion."
        )
        return {
            "response": response,
            "extracted_data": {
                "chief_complaint": session.chief_complaint,
                "symptoms": session.symptoms,
            },
            "conversation_complete": True,
        }

    def get_session(self, session_id: str) -> ChatbotSession | None:
        return self._sessions.get(session_id)


chatbot_service = ChatbotService()
