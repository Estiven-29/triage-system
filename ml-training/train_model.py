"""Entrena el modelo de clasificacion y lo guarda en backend/app/ml/model.joblib."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ml.train import MODEL_PATH, train_and_save  # noqa: E402


if __name__ == "__main__":
    _, report = train_and_save()
    print("Reporte de clasificacion (conjunto de prueba):\n")
    print(report)
    print(f"Modelo guardado en: {MODEL_PATH}")
