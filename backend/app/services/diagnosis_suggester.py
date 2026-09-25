"""
Sugerencias de diagnostico preliminar y acciones recomendadas.

Son heuristicas basadas en palabras clave y umbrales de signos vitales,
no un modelo de diagnostico entrenado ni un dispositivo medico. Sirven
como apoyo informativo para el personal, quien toma la decision final.
"""
from __future__ import annotations

_DIAGNOSIS_RULES: list[tuple[set[str], list[dict]]] = [
    (
        {"dolor toracico", "dificultad respiratoria"},
        [
            {"name": "Posible sindrome coronario agudo", "probability": 0.55},
            {"name": "Ansiedad / crisis de panico", "probability": 0.25},
            {"name": "Embolia pulmonar", "probability": 0.15},
        ],
    ),
    (
        {"fiebre", "tos"},
        [
            {"name": "Infeccion respiratoria (viral o bacteriana)", "probability": 0.6},
            {"name": "Neumonia", "probability": 0.2},
        ],
    ),
    (
        {"dolor abdominal", "nauseas"},
        [
            {"name": "Gastroenteritis", "probability": 0.45},
            {"name": "Apendicitis", "probability": 0.2},
        ],
    ),
    (
        {"dolor abdominal", "vomitos"},
        [
            {"name": "Gastroenteritis", "probability": 0.4},
            {"name": "Obstruccion intestinal", "probability": 0.15},
        ],
    ),
    (
        {"mareo", "perdida de conciencia"},
        [
            {"name": "Sincope vasovagal", "probability": 0.4},
            {"name": "Evento neurologico agudo (ACV/AIT)", "probability": 0.3},
        ],
    ),
    (
        {"cefalea"},
        [
            {"name": "Cefalea tensional", "probability": 0.5},
            {"name": "Migrana", "probability": 0.3},
        ],
    ),
]


def suggest_preliminary_diagnoses(symptoms: list[str]) -> list[dict]:
    symptom_set = set(symptoms)
    for trigger, diagnoses in _DIAGNOSIS_RULES:
        if trigger.issubset(symptom_set):
            return diagnoses
    if symptom_set:
        return [{"name": "Cuadro inespecifico, requiere evaluacion clinica", "probability": 0.4}]
    return []


def recommend_actions(classification: str, vital_signs: dict) -> list[str]:
    actions: list[str] = []

    if classification == "CRITICO":
        actions.append("Notificar de inmediato al personal medico")
        actions.append("Trasladar a area de reanimacion")
    elif classification == "URGENTE":
        actions.append("Reevaluar en un maximo de 30 minutos")
        actions.append("Realizar estudios complementarios segun el motivo de consulta")
    else:
        actions.append("Continuar monitoreo estandar")
        actions.append("Reevaluar si los sintomas empeoran")

    if vital_signs["spo2"] < 92:
        actions.append("Administrar oxigeno suplementario")
    if vital_signs["systolic_bp"] < 90:
        actions.append("Evaluar signos de shock e iniciar fluidoterapia")
    if vital_signs["temperature"] >= 38.5:
        actions.append("Considerar antipiretico y descartar foco infeccioso")
    if vital_signs["heart_rate"] > 130 or vital_signs["heart_rate"] < 45:
        actions.append("Solicitar electrocardiograma")

    return actions
