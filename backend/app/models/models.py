"""Modelos SQLAlchemy del sistema de triage."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    # Naive datetime (sin tzinfo) a proposito: SQLite no preserva timezone
    # en las columnas DateTime, asi que mantenemos todo naive-pero-UTC de
    # forma consistente en vez de mezclar aware/naive al comparar despues.
    return datetime.now(UTC).replace(tzinfo=None)


class MedicalStaff(Base):
    __tablename__ = "medical_staff"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    specialization = Column(String)
    license_number = Column(String)
    max_patient_capacity = Column(Integer, default=50)
    is_available = Column(Boolean, default=True)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=_uuid)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(String)
    gender = Column(String)
    created_at = Column(DateTime, default=utcnow)


class ChatSession(Base):
    """Estado de la conversacion de intake. Se guarda en BD (no en memoria)
    para que sobreviva reinicios, funcione con varios workers y no crezca
    sin limite en RAM. Comparte id con el Patient que la origino."""

    __tablename__ = "chat_sessions"

    id = Column(String, ForeignKey("patients.id"), primary_key=True)
    patient_name = Column(String, nullable=False)
    turn = Column(Integer, nullable=False, default=0)
    chief_complaint = Column(String, nullable=False, default="")
    symptoms = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class TriageAssessment(Base):
    """Resultado de clasificacion de un paciente en un momento dado."""

    __tablename__ = "triage_assessments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), index=True, nullable=False)
    patient_name = Column(String)
    chief_complaint = Column(String)
    symptoms = Column(JSON, default=list)
    vital_signs = Column(JSON, default=dict)

    classification = Column(String, nullable=False)  # CRITICO | URGENTE | NORMAL
    confidence = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False)
    complexity_index = Column(Integer, nullable=False)
    complexity_level = Column(String, nullable=False)
    preliminary_diagnoses = Column(JSON, default=list)
    recommended_actions = Column(JSON, default=list)

    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
