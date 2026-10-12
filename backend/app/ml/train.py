"""
Generacion de datos sinteticos y entrenamiento del modelo de clasificacion
de triage.

No existe un dataset clinico real disponible para este proyecto (por
razones obvias de privacidad de datos de salud), asi que las etiquetas de
entrenamiento se generan con una heuristica clinica publica y conocida: una
version simplificada del NEWS2 (National Early Warning Score 2, usado en el
NHS del Reino Unido) sobre signos vitales generados aleatoriamente dentro de
rangos fisiologicos plausibles, con ruido de etiqueta (~6%) para simular la
ambiguedad de casos reales. El modelo (Random Forest) SI se entrena y
evalua de forma real sobre estos datos; lo sintetico es el dataset, no el
entrenamiento.
"""
from __future__ import annotations

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

FEATURE_COLUMNS = [
    "heart_rate",
    "respiratory_rate",
    "systolic_bp",
    "diastolic_bp",
    "spo2",
    "temperature",
    "symptom_count",
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")


def _news2_points(value: float, bands: list[tuple[float, int]]) -> int:
    """Bandas contiguas definidas por su limite superior inclusivo, en orden
    ascendente. Asi no quedan huecos entre bandas para valores decimales
    (p. ej. 36.05 C), que antes caian fuera de todo rango y sumaban 3."""
    for upper, points in bands:
        if value <= upper:
            return points
    return bands[-1][1]


def early_warning_score(vital_signs) -> tuple[int, bool]:
    """Puntaje inspirado en NEWS2 (subset: no incluye O2 suplementario ni
    nivel de consciencia porque no se capturan en este formulario).

    Acepta un dict o una fila de pandas con las columnas de signos vitales.
    """
    inf = float("inf")
    rr_points = _news2_points(
        vital_signs["respiratory_rate"], [(8, 3), (11, 1), (20, 0), (24, 2), (inf, 3)]
    )
    spo2_points = _news2_points(vital_signs["spo2"], [(91, 3), (93, 2), (95, 1), (inf, 0)])
    sbp_points = _news2_points(
        vital_signs["systolic_bp"], [(90, 3), (100, 2), (110, 1), (219, 0), (inf, 3)]
    )
    hr_points = _news2_points(
        vital_signs["heart_rate"],
        [(40, 3), (50, 1), (90, 0), (110, 1), (130, 2), (inf, 3)],
    )
    temp_points = _news2_points(
        vital_signs["temperature"], [(35.0, 3), (36.0, 1), (38.0, 0), (39.0, 1), (inf, 2)]
    )

    points = [rr_points, spo2_points, sbp_points, hr_points, temp_points]
    total = sum(points)
    any_red_flag = any(p == 3 for p in points)
    return total, any_red_flag


def label_from_score(total: int, red_flag: bool) -> str:
    if red_flag or total >= 7:
        return "CRITICO"
    if total >= 3:
        return "URGENTE"
    return "NORMAL"


def generate_synthetic_dataset(n: int = 6000, seed: int = 42) -> pd.DataFrame:
    """
    Los signos vitales se muestrean de distribuciones normales centradas en
    valores fisiologicos tipicos (no uniformes sobre todo el rango posible),
    para que la poblacion sintetica se parezca a una sala de urgencias real:
    la mayoria de los casos son NORMAL/URGENTE y solo una minoria es
    CRITICO. Un muestreo uniforme sobre rangos extremos sobre-representa
    los casos graves y produce un dataset irrealista.
    """
    rng = np.random.default_rng(seed)

    is_febrile = rng.random(n) < 0.2
    temperature = np.where(
        is_febrile,
        rng.normal(38.3, 0.9, n),
        rng.normal(36.7, 0.35, n),
    )

    df = pd.DataFrame(
        {
            "heart_rate": np.clip(rng.normal(82, 18, n), 30, 200).round().astype(int),
            "respiratory_rate": np.clip(rng.normal(17, 3.5, n), 6, 45).round().astype(int),
            "systolic_bp": np.clip(rng.normal(122, 18, n), 60, 220).round().astype(int),
            "diastolic_bp": np.clip(rng.normal(76, 11, n), 35, 130).round().astype(int),
            "spo2": np.clip(rng.normal(97, 2.2, n), 70, 100).round().astype(int),
            "temperature": np.round(np.clip(temperature, 34.0, 41.5), 1),
            "symptom_count": rng.integers(0, 6, n),
        }
    )

    scores = df.apply(early_warning_score, axis=1)
    df["ews_total"] = [s[0] for s in scores]
    df["ews_red_flag"] = [s[1] for s in scores]
    df["classification"] = [
        label_from_score(t, r) for t, r in zip(df["ews_total"], df["ews_red_flag"])
    ]

    # Ruido de etiqueta: ~6% de los casos se "reclasifican" a la categoria
    # vecina, simulando la variabilidad de juicio clinico real.
    noisy_idx = rng.choice(n, size=int(n * 0.06), replace=False)
    order = ["NORMAL", "URGENTE", "CRITICO"]
    for i in noisy_idx:
        current = order.index(df.loc[i, "classification"])
        shift = rng.choice([-1, 1])
        new_idx = min(max(current + shift, 0), len(order) - 1)
        df.loc[i, "classification"] = order[new_idx]

    return df.drop(columns=["ews_total", "ews_red_flag"])


def train_and_save(n_samples: int = 6000, seed: int = 42, model_path: str = MODEL_PATH):
    df = generate_synthetic_dataset(n_samples, seed)
    X = df[FEATURE_COLUMNS]
    y = df["classification"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200, max_depth=10, random_state=seed, class_weight="balanced"
    )
    model.fit(X_train, y_train)

    report = classification_report(y_test, model.predict(X_test))

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)

    return model, report


if __name__ == "__main__":
    _, report = train_and_save()
    print(report)
    print(f"Modelo guardado en: {MODEL_PATH}")
