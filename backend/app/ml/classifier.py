"""Carga del modelo entrenado y prediccion en tiempo de inferencia."""
from __future__ import annotations

import os

import joblib
import numpy as np
import pandas as pd

from .train import FEATURE_COLUMNS, MODEL_PATH, train_and_save

_model = None


def load_model():
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        # Primera ejecucion: entrenamos automaticamente para que el backend
        # funcione "out of the box" sin pasos manuales previos.
        train_and_save()

    _model = joblib.load(MODEL_PATH)
    return _model


def classify(vital_signs: dict, symptom_count: int) -> tuple[str, float]:
    model = load_model()
    row = {col: vital_signs[col] for col in FEATURE_COLUMNS if col != "symptom_count"}
    row["symptom_count"] = symptom_count
    features = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    proba = model.predict_proba(features)[0]
    idx = int(np.argmax(proba))
    classification = model.classes_[idx]
    confidence = float(proba[idx])
    return classification, confidence
