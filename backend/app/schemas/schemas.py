"""Esquemas Pydantic para requests/responses de la API."""
from typing import Optional

from pydantic import BaseModel, Field


# ---------- Chatbot ----------

class PatientIntakeData(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = "other"


class ChatStartResponse(BaseModel):
    session_id: str
    message: str


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str


class ExtractedData(BaseModel):
    chief_complaint: str
    symptoms: list[str]


class ChatMessageResponse(BaseModel):
    response: str
    extracted_data: Optional[ExtractedData] = None
    conversation_complete: bool = False


# ---------- Triage / clasificacion ----------

class VitalSigns(BaseModel):
    heart_rate: int = Field(ge=0, le=300)
    respiratory_rate: int = Field(ge=0, le=100)
    systolic_bp: int = Field(ge=0, le=300)
    diastolic_bp: int = Field(ge=0, le=200)
    spo2: int = Field(ge=0, le=100)
    temperature: float = Field(ge=25.0, le=45.0)


class TriageClassifyRequest(BaseModel):
    patient_id: str
    vital_signs: VitalSigns
    chief_complaint: str = ""
    symptoms: list[str] = []


class PreliminaryDiagnosis(BaseModel):
    name: str
    probability: float


class TriageClassifyResponse(BaseModel):
    classification: str
    confidence: float
    # True si la regla de seguridad (alerta roja NEWS2) elevo la
    # clasificacion del modelo a CRITICO.
    safety_override: bool = False
    risk_score: int
    tiss28_score: int
    complexity_level: str
    preliminary_diagnoses: list[PreliminaryDiagnosis]
    recommended_actions: list[str]


# ---------- Dashboard ----------

class SystemMetrics(BaseModel):
    totalPatients: int
    critical: int
    urgent: int
    normal: int
    avgWaitTime: float
    mlConfidence: float
    avgTiss28: float


class ActivePatient(BaseModel):
    id: str
    name: str
    age: Optional[int] = None
    category: str
    riskScore: int
    tiss28: int
    waitTime: int
    assignedTo: str
    complaint: str


class DashboardMetricsResponse(BaseModel):
    systemMetrics: SystemMetrics
    tiss28Distribution: list[dict]
