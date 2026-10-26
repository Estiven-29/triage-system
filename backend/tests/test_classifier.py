from app.ml.classifier import classify
from app.ml.train import early_warning_score

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
    label, confidence, override = classify(NORMAL_VITALS, symptom_count=0)
    assert label in {"NORMAL", "URGENTE", "CRITICO"}
    assert 0.0 <= confidence <= 1.0
    assert override is False


def test_classify_flags_clearly_critical_vitals_as_higher_severity():
    normal_label, _, _ = classify(NORMAL_VITALS, symptom_count=0)
    critical_label, _, _ = classify(CRITICAL_VITALS, symptom_count=4)

    order = {"NORMAL": 0, "URGENTE": 1, "CRITICO": 2}
    assert order[critical_label] > order[normal_label]


def test_single_red_flag_vital_is_always_critical():
    # Todo normal salvo hipotermia (34 C): el modelo por si solo no lo marca
    # CRITICO, pero una sola alerta roja NEWS2 basta para que la regla de
    # seguridad lo garantice.
    vitals = {**NORMAL_VITALS, "temperature": 34.0}
    label, _, _ = classify(vitals, symptom_count=0)
    assert label == "CRITICO"


def test_early_warning_score_has_no_gaps_for_decimal_values():
    # Antes 36.05 C caia entre las bandas (36.0, 36.1) y sumaba 3 puntos.
    total, red_flag = early_warning_score({**NORMAL_VITALS, "temperature": 36.05})
    assert total == 0
    assert red_flag is False
