from app.ml.classifier import classify

NORMAL_VITALS = {
    "heart_rate": 72,
    "respiratory_rate": 15,
    "systolic_bp": 118,
    "diastolic_bp": 76,
    "spo2": 98,
    "temperature": 36.7,
}

CRITICAL_VITALS = {
    "heart_rate": 150,
    "respiratory_rate": 30,
    "systolic_bp": 78,
    "diastolic_bp": 48,
    "spo2": 84,
    "temperature": 39.5,
}


def test_classify_returns_valid_label_and_confidence():
    label, confidence = classify(NORMAL_VITALS, symptom_count=0)
    assert label in {"NORMAL", "URGENTE", "CRITICO"}
    assert 0.0 <= confidence <= 1.0


def test_classify_flags_clearly_critical_vitals_as_higher_severity():
    normal_label, _ = classify(NORMAL_VITALS, symptom_count=0)
    critical_label, _ = classify(CRITICAL_VITALS, symptom_count=4)

    order = {"NORMAL": 0, "URGENTE": 1, "CRITICO": 2}
    assert order[critical_label] > order[normal_label]
