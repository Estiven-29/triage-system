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
from datetime import timedelta

from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.models import ChatSession, Patient, utcnow

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


class ChatSessionNotFound(KeyError):
    """La sesion no existe o expiro por inactividad."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ChatbotService:
    """Sesiones persistidas en la tabla chat_sessions. Al guardarse en BD no
    crecen sin limite en memoria, sobreviven a reinicios y funcionan con
    varios workers. Las que pasan ttl_minutes sin actividad expiran y se
    borran de forma perezosa al iniciar sesiones nuevas."""

    def __init__(self, ttl_minutes: int = settings.CHAT_SESSION_TTL_MINUTES):
        self.ttl = timedelta(minutes=ttl_minutes)

    def _is_expired(self, session: ChatSession) -> bool:
        return session.updated_at < utcnow() - self.ttl

    def purge_expired(self, db: Session) -> int:
        cutoff = utcnow() - self.ttl
        return db.query(ChatSession).filter(ChatSession.updated_at < cutoff).delete()

    def start_session(self, db: Session, patient: Patient) -> str:
        """Crea la sesion para un paciente ya agregado a `db` y devuelve el
        saludo. No hace commit: el llamador confirma paciente y sesion juntos."""
        self.purge_expired(db)
        patient_name = f"{patient.first_name} {patient.last_name}".strip()
        db.add(ChatSession(id=patient.id, patient_name=patient_name))
        return (
            f"Hola {patient_name}, soy el asistente de admision. "
            "Cuentame en tus palabras: ¿cual es el motivo principal de tu "
            "consulta y que sintomas presentas?"
        )

    def handle_message(self, db: Session, session_id: str, message: str) -> dict:
        session = db.get(ChatSession, session_id)
        if session is None:
            raise ChatSessionNotFound(f"Sesion de chatbot no encontrada: {session_id}")
        if self._is_expired(session):
            db.delete(session)
            db.commit()
            raise ChatSessionNotFound(f"La sesion de chatbot expiro: {session_id}")

        session.turn += 1

        if session.turn == 1:
            session.chief_complaint = message.strip()
            session.symptoms = extract_symptoms(message)
            response = (
                "Entiendo. ¿Desde hace cuanto tiempo tienes estos sintomas "
                "y en una escala del 1 al 10, que tan intensos son?"
            )
            complete = False
        else:
            # Turno 2: cerramos la conversacion y volvemos a extraer por si
            # el paciente menciono sintomas nuevos en este mensaje.
            session.symptoms = extract_symptoms(session.chief_complaint, message)
            response = (
                "Gracias por la informacion. Ahora vamos a registrar tus signos "
                "vitales para completar la clasificacion."
            )
            complete = True

        db.commit()
        return {
            "response": response,
            "extracted_data": {
                "chief_complaint": session.chief_complaint,
                "symptoms": session.symptoms,
            },
            "conversation_complete": complete,
        }


chatbot_service = ChatbotService()
