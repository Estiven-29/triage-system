"""
Genera el dataset sintetico de entrenamiento y lo guarda como CSV.

La logica de generacion vive en backend/app/ml/train.py para que el mismo
codigo lo pueda usar el backend (auto-entrenamiento al arrancar) y estos
scripts de exploracion/documentacion del pipeline de ML.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ml.train import generate_synthetic_dataset  # noqa: E402

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "synthetic_triage_data.csv")


if __name__ == "__main__":
    df = generate_synthetic_dataset()
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Dataset sintetico generado: {len(df)} filas")
    print(df["classification"].value_counts())
    print(f"Guardado en: {OUTPUT_PATH}")
