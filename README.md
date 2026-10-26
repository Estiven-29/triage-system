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
| Dashboard (Carga de Trabajo TISS-28, Analítica) | **Parcialmente ilustrativo** — la asignación y carga del personal son reales (asignación automática por menor carga relativa; requiere personal creado con `init_db.py`), pero la tendencia horaria sigue siendo un dato de ejemplo (se indica en la UI); el radar de "Rendimiento del Modelo ML" sí usa métricas reales. |

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

### Acceso del personal (login)

El intake del paciente (chatbot y clasificación) es público, porque se usa
en el puesto de admisión. El **dashboard**, las **altas** y el **WebSocket**
muestran datos de todos los pacientes y requieren iniciar sesión.

`python init_db.py` crea 4 cuentas de ejemplo (`DOC001` a `DOC004`) con la
contraseña `triage-demo` (configurable con `DEMO_STAFF_PASSWORD`). Las
sesiones son tokens JWT firmados con `SECRET_KEY`: defínela fuera de
desarrollo, o las sesiones se invalidarán en cada reinicio.

### Migraciones de base de datos (Alembic)

El esquema se gestiona con migraciones de Alembic (`backend/migrations/`).
El backend aplica las pendientes al arrancar (`alembic upgrade head`), así
que normalmente no hay que hacer nada. Si cambias un modelo en
`app/models/models.py`, genera la migración correspondiente:

```bash
cd backend
alembic revision --autogenerate -m "describe el cambio"
alembic upgrade head
```

El test `tests/test_migrations.py` falla si los modelos y las migraciones
no coinciden.

Si tienes una base de datos creada con una versión anterior del proyecto
(sin migraciones), el backend se niega a arrancar con un mensaje claro: si
es de desarrollo, bórrala (`triage.db`); si ya tiene el esquema actual,
márcala con `alembic stamp head`.

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

Antes de cada commit o PR, corre todos los chequeos (lint y tests del
backend, tests y build del frontend) con:

```bash
./check.sh            # todo
./check.sh backend    # solo backend
./check.sh frontend   # solo frontend
```

En Windows, ejecútalo desde Git Bash (incluido con Git para Windows), con el
entorno virtual del backend activado. Es lo mismo que hace el workflow `.github/workflows/ci.yml`, que está
configurado para correr solo de forma manual. El encabezado del script explica
cómo probar también contra PostgreSQL con una base desechable.

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
- `POST /api/triage/classify` — clasifica al paciente con los signos vitales y lo asigna al profesional disponible con menor carga
- `POST /api/auth/login` — inicia sesión del personal y devuelve un token JWT
- `GET /api/auth/me` — datos del personal con la sesión actual 🔒
- `POST /api/triage/assessments/{id}/discharge` 🔒 — da de alta al paciente (deja de estar activo y libera carga)
- `GET /api/dashboard/metrics` 🔒 — métricas agregadas de los pacientes activos (sin alta)
- `GET /api/dashboard/active-patients` 🔒 — lista de pacientes activos
- `GET /api/dashboard/staff-workload` 🔒 — carga actual de cada profesional
- `WS /ws/triage` 🔒 — notifica cuando se clasifica o da de alta a un paciente (el token se envía como primer mensaje)

🔒 = requiere `Authorization: Bearer <token>` del personal.

## Variables de entorno (backend)

Ver `backend/.env.example`. Por defecto usa SQLite y no requiere configuración.
