"""Endpoints del chatbot de intake."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..models.models import Patient
from ..schemas.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatStartResponse,
    PatientIntakeData,
)
from ..services.chatbot_service import ChatSessionNotFound, chatbot_service

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


@router.post("/start", response_model=ChatStartResponse)
def start_chat(patient_data: PatientIntakeData, db: Session = Depends(get_db)):
    patient = Patient(
        first_name=patient_data.first_name,
        last_name=patient_data.last_name,
        date_of_birth=(
            patient_data.date_of_birth.isoformat() if patient_data.date_of_birth else None
        ),
        gender=patient_data.gender,
    )
    db.add(patient)
    db.flush()  # asigna patient.id, que tambien es el id de la sesion
    greeting = chatbot_service.start_session(db, patient)
    db.commit()

    return ChatStartResponse(session_id=patient.id, message=greeting)


@router.post("/message", response_model=ChatMessageResponse)
def send_message(payload: ChatMessageRequest, db: Session = Depends(get_db)):
    try:
        result = chatbot_service.handle_message(db, payload.session_id, payload.message)
    except ChatSessionNotFound as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    return ChatMessageResponse(**result)
