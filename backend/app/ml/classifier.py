"""Carga del modelo entrenado y prediccion en tiempo de inferencia."""
from __future__ import annotations

import os
import threading

import joblib
import numpy as np
import pandas as pd

from .train import FEATURE_COLUMNS, MODEL_PATH, early_warning_score, train_and_save

_model = None
_model_lock = threading.Lock()


def load_model():
    global _model
    if _model is not None:
        return _model

    # El lock evita que dos peticiones concurrentes entrenen el modelo a la
    # vez si todavia no existe en disco.
    with _model_lock:
        if _model is None:
            if not os.path.exists(MODEL_PATH):
                # Primera ejecucion: entrenamos automaticamente para que el
                # backend funcione "out of the box" sin pasos manuales previos.
                train_and_save()
            _model = joblib.load(MODEL_PATH)
    return _model


def classify(vital_signs: dict, symptom_count: int) -> tuple[str, float, bool]:
    """Devuelve (clasificacion, confianza, safety_override).

    Sobre la prediccion del modelo se aplica una regla de seguridad: si los
    signos vitales tienen una alerta roja tipo NEWS2 (algun parametro con 3
    puntos) o un puntaje total >= 7, el paciente se clasifica CRITICO aunque
    el modelo diga otra cosa. En triage un falso negativo es el peor error
    posible, y el modelo se entrena con ruido de etiqueta a proposito.
    """
    model = load_model()
    row = {col: vital_signs[col] for col in FEATURE_COLUMNS if col != "symptom_count"}
    row["symptom_count"] = symptom_count
    features = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    proba = model.predict_proba(features)[0]
    idx = int(np.argmax(proba))
    classification = str(model.classes_[idx])
    confidence = float(proba[idx])

    total, red_flag = early_warning_score(vital_signs)
    if (red_flag or total >= 7) and classification != "CRITICO":
        critical_idx = list(model.classes_).index("CRITICO")
        return "CRITICO", float(proba[critical_idx]), True

    return classification, confidence, False
