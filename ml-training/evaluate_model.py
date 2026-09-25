"""Evalua el modelo guardado contra un nuevo conjunto sintetico (semilla distinta)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import classification_report, cohen_kappa_score, confusion_matrix  # noqa: E402

from app.ml.train import FEATURE_COLUMNS, MODEL_PATH, generate_synthetic_dataset  # noqa: E402


if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH):
        raise SystemExit("No se encontro el modelo. Ejecuta train_model.py primero.")

    model = joblib.load(MODEL_PATH)

    # Semilla distinta a la usada en entrenamiento, para una evaluacion
    # honesta sobre datos "nuevos".
    df = generate_synthetic_dataset(n=1500, seed=99)
    X = df[FEATURE_COLUMNS]
    y_true = df["classification"]
    y_pred = model.predict(X)

    print("Matriz de confusion (filas=real, columnas=prediccion):")
    labels = sorted(y_true.unique())
    print(labels)
    print(confusion_matrix(y_true, y_pred, labels=labels))
    print()
    print(classification_report(y_true, y_pred))

    proba = model.predict_proba(X)
    avg_confidence = np.max(proba, axis=1).mean()
    kappa = cohen_kappa_score(y_true, y_pred)
    print(f"Confianza promedio (max probabilidad): {avg_confidence * 100:.1f}%")
    print(f"Cohen's Kappa: {kappa:.2f}")
