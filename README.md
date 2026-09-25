# Sistema de Triage Inteligente (FastAPI + React)

Proyecto educativo/portafolio: plataforma de apoyo a la clasificación de
pacientes en un servicio de urgencias. **No es un dispositivo médico ni
debe usarse para decisiones clínicas reales.**

Flujo: se registra un paciente, un chatbot de intake (basado en reglas)
recoge el motivo de consulta y los síntomas, se capturan los signos
vitales, y un modelo de Machine Learning (Random Forest, entrenado sobre
datos sintéticos) clasifica el caso como `CRITICO` / `URGENTE` / `NORMAL`,
con un índice de complejidad inspirado en TISS-28, diagnósticos
preliminares sugeridos por reglas y acciones recomendadas. El dashboard
muestra los pacientes ya clasificados con datos reales (no simulados).

## Qué es real y qué es una simplificación (léelo antes de usar el proyecto)

| Componente | Estado |
|---|---|
| Clasificación ML | **Real**: Random Forest entrenado y evaluado con `scikit-learn` (~91% accuracy, ~91% recall en CRÍTICO sobre el conjunto de evaluación sintético). |
| Dataset de entrenamiento | **Sintético**: no existe un dataset clínico real disponible (por privacidad de datos de salud). Se genera con una heurística basada en una versión simplificada del NEWS2 (National Early Warning Score) + ruido de etiqueta. Ver `backend/app/ml/train.py`. |
| Chatbot de intake | **Basado en reglas** (extracción de síntomas por palabras clave + maquina de estados de 2 turnos), no un LLM generativo. |
| Índice "TISS-28" | **Aproximación**, no la escala clínica real (que requiere un checklist de 28 intervenciones de enfermería, dato que esta app no captura). Ver el docstring de `backend/app/services/complexity.py`. |
| Diagnósticos preliminares | **Heurística por palabras clave**, no un modelo de diagnóstico entrenado. |
| Dashboard (Vista General) | **Real**, calculado desde la base de datos con los pacientes efectivamente clasificados. |
| Dashboard (Carga de Trabajo TISS-28, Analítica) | **Parcialmente ilustrativo** — la asignación de personal y la tendencia horaria son datos de ejemplo (se indica en la UI); el radar de "Rendimiento del Modelo ML" sí usa métricas reales. |

## Arquitectura

- **Backend**: FastAPI + SQLAlchemy (SQLite por defecto, Postgres opcional) + scikit-learn.
- **Frontend**: React 18 (Create React App + CRACO) + Tailwind CSS + Recharts.
- **Comunicación en tiempo real**: WebSocket (`/ws/triage`) para refrescar el dashboard cuando se clasifica un paciente nuevo.

```
triage-system/
├── backend/
│   ├── app/
│   │   ├── api/          # endpoints (chatbot, triage, dashboard, websocket)
│   │   ├── services/     # chatbot, complejidad, sugerencias de diagnóstico
│   │   ├── ml/           # generación de datos sintéticos, entrenamiento, inferencia
│   │   ├── models/       # modelos SQLAlchemy
│   │   ├── schemas/      # esquemas Pydantic
│   │   └── main.py
│   ├── tests/            # pytest
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── components/   # PatientIntake, TriageDashboard
│       └── services/     # cliente HTTP + WebSocket
├── ml-training/          # scripts CLI (usan la misma lógica que el backend)
└── docker-compose.yml    # backend + Postgres
```

## Puesta en marcha local

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

No hace falta ejecutar nada más: si no existe un modelo entrenado, el
backend lo entrena automáticamente en el primer arranque (unos segundos)
y crea la base de datos SQLite (`triage.db`) en `backend/`.

Documentación interactiva: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm start
```

Abre http://localhost:3000. El backend debe estar corriendo en el puerto 8000
(o define `REACT_APP_API_URL` en un `.env` si usas otro puerto/host).

### Con Docker (backend + Postgres)

```bash
docker compose up --build
```

## Scripts de Machine Learning

```bash
cd backend && .venv\Scripts\activate
python ../ml-training/data_preparation.py   # genera el dataset sintético (CSV)
python ../ml-training/train_model.py        # entrena y guarda el modelo
python ../ml-training/evaluate_model.py     # evalúa con un conjunto nuevo (semilla distinta)
```

## Pruebas

```bash
cd backend && .venv\Scripts\activate
pytest -v
```

Cubre: el índice de complejidad, el chatbot (extracción de síntomas y flujo
de 2 turnos), el clasificador ML, y un test de integración end-to-end sobre
la API (intake → chatbot → clasificación → dashboard).

## Endpoints principales

- `POST /api/chatbot/start` — inicia la sesión de intake
- `POST /api/chatbot/message` — envía un mensaje al chatbot
- `POST /api/triage/classify` — clasifica al paciente con los signos vitales
- `GET /api/dashboard/metrics` — métricas agregadas de los últimos casos
- `GET /api/dashboard/active-patients` — lista de pacientes recientes
- `WS /ws/triage` — notifica cuando se clasifica un paciente nuevo

## Variables de entorno (backend)

Ver `backend/.env.example`. Por defecto usa SQLite y no requiere configuración.
