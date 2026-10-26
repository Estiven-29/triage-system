"""
Indice de complejidad de cuidados, inspirado en la metodologia TISS-28.

IMPORTANTE (limitacion real, no un bug): la escala TISS-28 clinica real se
calcula a partir de un checklist de 28 intervenciones de enfermeria
realizadas (ventilacion mecanica, drogas vasoactivas, lineas arteriales,
dialisis, etc.), no a partir de los signos vitales crudos. Como esta app
solo captura signos vitales y sintomas reportados (no un registro de
intervenciones), este modulo calcula una *aproximacion* basada en la
severidad de los signos vitales y la cantidad de sintomas, en el mismo
rango 0-45+ que usa la escala real, para poder alimentar el dashboard.
No debe interpretarse como un TISS-28 clinicamente valido.
"""
from __future__ import annotations


def _points(value: float, low: float, high: float, step: float, max_points: int) -> int:
    """Puntos por desviacion respecto a un rango normal [low, high]."""
    if low <= value <= high:
        return 0
    distance = (low - value) if value < low else (value - high)
    return min(max_points, int(distance // step) + 1)


def estimate_complexity_index(vital_signs: dict, symptom_count: int) -> int:
    score = 0
    score += _points(vital_signs["heart_rate"], 60, 100, 10, 6)
    score += _points(vital_signs["respiratory_rate"], 12, 20, 4, 6)
    score += _points(vital_signs["spo2"], 95, 100, 2, 8)
    score += _points(vital_signs["systolic_bp"], 90, 140, 15, 6)
    score += _points(vital_signs["temperature"], 36.0, 37.8, 0.5, 6)
    score += min(6, symptom_count * 2)
    return score


# Niveles de complejidad: (limite superior inclusivo, nombre, etiqueta del
# rango). Fuente unica para la clasificacion y los buckets del dashboard.
COMPLEXITY_LEVELS: list[tuple[float, str, str]] = [
    (10, "Baja", "0-10"),
    (20, "Moderada", "11-20"),
    (30, "Alta", "21-30"),
    (40, "Muy Alta", "31-40"),
    (float("inf"), "Critica", "41+"),
]


def complexity_level_index(index: int) -> int:
    for position, (upper, _name, _range) in enumerate(COMPLEXITY_LEVELS):
        if index <= upper:
            return position
    return len(COMPLEXITY_LEVELS) - 1


def complexity_level(index: int) -> str:
    return COMPLEXITY_LEVELS[complexity_level_index(index)][1]
