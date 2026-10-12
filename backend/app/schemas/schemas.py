"""Esquemas Pydantic para requests/responses de la API."""
from datetime import date, datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

TriageCategory = Literal["CRITICO", "URGENTE", "NORMAL"]

# Texto con espacios recortados y longitud acotada, para no aceptar nombres
# vacios ni payloads arbitrariamente grandes.
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
SymptomName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


# ---------- Chatbot ----------

class PatientIntakeData(BaseModel):
    first_name: Name
    last_name: Name
    date_of_birth: Optional[date] = None
    gender: Literal["male", "female", "other"] = "other"

    @field_validator("date_of_birth")
    @classmethod
    def _dob_not_in_future(cls, value: Optional[date]) -> Optional[date]:
        if value is not None and value > date.today():
            raise ValueError("la fecha de nacimiento no puede ser futura")
        return value


class ChatStartResponse(BaseModel):
    session_id: str
    message: str


class ChatMessageRequest(BaseModel):
    session_id: str = Field(max_length=64)
    message: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]


class ExtractedData(BaseModel):
    chief_complaint: str
    symptoms: list[str]


class ChatMessageResponse(BaseModel):
    response: str
    extracted_data: Optional[ExtractedData] = None
    conversation_complete: bool = False


# ---------- Triage / clasificacion ----------

class VitalSigns(BaseModel):
    """Rangos fisiologicamente posibles en un paciente que llega a triage.
    Valores como FC 0 o SpO2 0 son casi siempre errores de captura; un
    paciente en paro no pasa por este formulario. Mantener sincronizado con
    VITAL_SIGN_LIMITS en frontend/src/components/PatientIntake.jsx."""

    heart_rate: int = Field(ge=20, le=250)
    respiratory_rate: int = Field(ge=4, le=60)
    systolic_bp: int = Field(ge=40, le=300)
    diastolic_bp: int = Field(ge=20, le=200)
    spo2: int = Field(ge=50, le=100)
    temperature: float = Field(ge=25.0, le=45.0)

    @model_validator(mode="after")
    def _diastolic_below_systolic(self) -> "VitalSigns":
        if self.diastolic_bp >= self.systolic_bp:
            raise ValueError("la presion diastolica debe ser menor que la sistolica")
        return self


class TriageClassifyRequest(BaseModel):
    patient_id: str = Field(max_length=64)
    vital_signs: VitalSigns
    chief_complaint: str = Field(default="", max_length=1000)
    symptoms: list[SymptomName] = Field(default_factory=list, max_length=30)


class PreliminaryDiagnosis(BaseModel):
    name: str
    probability: float


class TriageClassifyResponse(BaseModel):
    classification: TriageCategory
    confidence: float
    # True si la regla de seguridad (alerta roja NEWS2) elevo la
    # clasificacion del modelo a CRITICO.
    safety_override: bool = False
    risk_score: int
    tiss28_score: int
    complexity_level: str
    preliminary_diagnoses: list[PreliminaryDiagnosis]
    recommended_actions: list[str]
    # Nombre del profesional asignado automaticamente, o None si nadie tenia
    # capacidad disponible.
    assigned_to: Optional[str] = None


class DischargeResponse(BaseModel):
    id: int
    discharged_at: datetime


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
    category: TriageCategory
    riskScore: int
    tiss28: int
    waitTime: int
    assignedTo: str
    complaint: str


class StaffWorkload(BaseModel):
    id: int
    name: str
    role: str
    tiss28Load: int
    capacity: int
    patients: int
    available: bool


class DashboardMetricsResponse(BaseModel):
    systemMetrics: SystemMetrics
    tiss28Distribution: list[dict]
