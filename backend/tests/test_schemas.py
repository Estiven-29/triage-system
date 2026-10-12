from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.schemas import (
    ChatMessageRequest,
    PatientIntakeData,
    TriageClassifyRequest,
    VitalSigns,
)

VALID_VITALS = {
    "heart_rate": 80,
    "respiratory_rate": 16,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "spo2": 98,
    "temperature": 36.8,
}


def test_valid_vitals_are_accepted():
    assert VitalSigns(**VALID_VITALS).spo2 == 98


@pytest.mark.parametrize(
    "field, value",
    [
        ("heart_rate", 0),
        ("heart_rate", 251),
        ("respiratory_rate", 0),
        ("systolic_bp", 30),
        ("spo2", 0),
        ("spo2", 101),
        ("temperature", 50.0),
    ],
)
def test_implausible_vitals_are_rejected(field, value):
    with pytest.raises(ValidationError):
        VitalSigns(**{**VALID_VITALS, field: value})


def test_diastolic_must_be_below_systolic():
    with pytest.raises(ValidationError, match="diastolica"):
        VitalSigns(**{**VALID_VITALS, "systolic_bp": 90, "diastolic_bp": 95})


def test_names_are_stripped_and_required():
    data = PatientIntakeData(first_name="  Ana ", last_name="Gomez")
    assert data.first_name == "Ana"
    with pytest.raises(ValidationError):
        PatientIntakeData(first_name="   ", last_name="Gomez")
    with pytest.raises(ValidationError):
        PatientIntakeData(first_name="A" * 101, last_name="Gomez")


def test_invalid_gender_and_future_birth_date_are_rejected():
    with pytest.raises(ValidationError):
        PatientIntakeData(first_name="Ana", last_name="Gomez", gender="x")
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError, match="futura"):
        PatientIntakeData(first_name="Ana", last_name="Gomez", date_of_birth=tomorrow)


def test_chat_message_length_is_bounded():
    with pytest.raises(ValidationError):
        ChatMessageRequest(session_id="s", message="   ")
    with pytest.raises(ValidationError):
        ChatMessageRequest(session_id="s", message="x" * 1001)


def test_symptom_list_is_bounded():
    with pytest.raises(ValidationError):
        TriageClassifyRequest(
            patient_id="p", vital_signs=VALID_VITALS, symptoms=["fiebre"] * 31
        )
