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
from ..services.chatbot_service import chatbot_service

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


@router.post("/start", response_model=ChatStartResponse)
def start_chat(patient_data: PatientIntakeData, db: Session = Depends(get_db)):
    full_name = f"{patient_data.first_name} {patient_data.last_name}".strip()
    session_id, greeting = chatbot_service.start_session(full_name)

    patient = Patient(
        id=session_id,
        first_name=patient_data.first_name,
        last_name=patient_data.last_name,
        date_of_birth=patient_data.date_of_birth,
        gender=patient_data.gender,
    )
    db.add(patient)
    db.commit()

    return ChatStartResponse(session_id=session_id, message=greeting)


@router.post("/message", response_model=ChatMessageResponse)
def send_message(payload: ChatMessageRequest):
    try:
        result = chatbot_service.handle_message(payload.session_id, payload.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ChatMessageResponse(**result)
