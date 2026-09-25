from app.services.complexity import complexity_level, estimate_complexity_index

NORMAL_VITALS = {
    "heart_rate": 75,
    "respiratory_rate": 16,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "spo2": 98,
    "temperature": 36.8,
}

CRITICAL_VITALS = {
    "heart_rate": 160,
    "respiratory_rate": 32,
    "systolic_bp": 75,
    "diastolic_bp": 45,
    "spo2": 82,
    "temperature": 39.8,
}


def test_normal_vitals_have_low_complexity():
    index = estimate_complexity_index(NORMAL_VITALS, symptom_count=0)
    assert index <= 10
    assert complexity_level(index) == "Baja"


def test_critical_vitals_have_high_complexity():
    index = estimate_complexity_index(CRITICAL_VITALS, symptom_count=3)
    assert index > estimate_complexity_index(NORMAL_VITALS, symptom_count=0)
    assert complexity_level(index) in {"Alta", "Muy Alta", "Critica"}


def test_complexity_level_boundaries():
    assert complexity_level(10) == "Baja"
    assert complexity_level(11) == "Moderada"
    assert complexity_level(41) == "Critica"
