# Sistema de Triaje Inteligente (FastAPI + React)

Plataforma para la clasificación de pacientes en urgencias combinando modelos de Machine Learning, cálculo TISS-28 y una interfaz moderna en React. Incluye API REST, WebSocket para interacción en tiempo real, scripts de entrenamiento de modelos y preparación de datos.

## Tabla de contenidos
- Descripción general
- Características
- Arquitectura
- Requisitos
- Estructura del proyecto
- Puesta en marcha en PC local (Windows)
- Scripts de Machine Learning
- API y documentación
- Pruebas
- Buenas prácticas y seguridad
- Problemas comunes

## Descripción general
Este sistema ayuda a priorizar pacientes en un servicio de urgencias mediante:
- Clasificación automática basada en ML (scikit-learn / XGBoost / LightGBM).
- Cálculo del índice **TISS-28** para estimar carga de cuidados.
- Integración con FHIR para interoperabilidad clínica.
- Panel de control en React para visualización, ingreso de pacientes y seguimiento.

## Características
- API en **FastAPI** (rápida y tipada) con CORS configurado para el frontend.
- Modelos de datos con **Pydantic** y persistencia con **SQLAlchemy**.
- Scripts para **preparación de datos**, **entrenamiento** y **evaluación** de modelos.
- Dashboard en **React** (Create React App) y gráficos con **Recharts**.
- Documentación automática Swagger en `http://localhost:8000/docs`.

## Arquitectura
- **Frontend**: React (CRA), Tailwind (configurado), servicios Axios.
- **Backend**: FastAPI, Pydantic, SQLAlchemy, Uvicorn, integración FHIR.
- **Base de datos**: PostgreSQL (recomendado), se puede usar SQLite para desarrollo rápido.
- **ML**: scikit-learn, XGBoost, LightGBM; seguimiento opcional con MLflow.

## Requisitos
- **Windows 10/11**.
- **Node.js** `>= 18` y **npm** `>= 9`.
- **Python** `>= 3.10` (recomendado `3.12`).
- **PostgreSQL** `>= 14` (o SQLite para pruebas).

## Estructura del proyecto
```
triage-system/
├── backend/
│   ├── init_db.py              # utilidades de inicialización de BD
│   └── ...                     # (código de API FastAPI)
├── frontend/
│   ├── src/                    # componentes y servicios de React
│   └── ...
└── ml-training/
    ├── data_preparation.py     # limpieza y feature engineering
    ├── train_model.py          # entrenamiento y persistencia de modelos
    └── evaluate_model.py       # métricas y evaluación
```

> Nota: Si tu código de backend está dentro de `backend/venv/app`, se recomienda **moverlo** a `backend/app` para evitar confusiones (los entornos virtuales no deben contener código fuente). Asegúrate de ajustar la ruta de ejecución de Uvicorn según corresponda.

## Puesta en marcha en PC local (Windows)

### 1) Clonar el repositorio

```powershell
# Si aún no lo has clonado (usa tu URL)
git clone https://github.com/Estiven-29/triage-system.git
cd triage-system
```

### 2) Backend (FastAPI)

1. Crear entorno virtual (recomendado dentro de `backend/.venv`):
   ```powershell
   cd backend
   py -3.12 -m venv .venv   # o: python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Instalar dependencias:
   - Si tienes `backend/requirements.txt`:
     ```powershell
     pip install -r requirements.txt
     ```
   - En su defecto, instala paquetes comunes manualmente (ejemplo mínimo):
     ```powershell
     pip install fastapi uvicorn[standard] sqlalchemy pydantic python-dotenv requests psycopg2-binary
     pip install scikit-learn xgboost lightgbm pandas numpy
     ```

3. Configurar variables de entorno (`backend/.env`):
   ```dotenv
   DATABASE_URL=postgresql://usuario:password@localhost:5432/triage_db
   FRONTEND_URL=http://localhost:3000
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
   SECRET_KEY=una_clave_segura
   FHIR_BASE_URL=https://servidor-fhir-ejemplo
   ```

4. Inicializar la base de datos (opcional):
   ```powershell
   python init_db.py
   ```

5. Ejecutar el servidor (ajusta el módulo según tu estructura):
   ```powershell
   # Si tu app está en backend/app/main.py
   uvicorn app.main:app --reload --port 8000
   
   # Si aún está en backend/venv/app/main.py (no recomendado)
   uvicorn app.main:app --reload --port 8000 --app-dir ./venv/app
   ```

### 3) Frontend (React)

1. Instalar dependencias y arrancar:
   ```powershell
   cd ../frontend
   npm install
   npm start
   ```

2. Acceder a la UI:
   - `http://localhost:3000`
   - El `package.json` ya tiene `proxy: "http://localhost:8000"`, por lo que las llamadas al backend funcionan sin configurar CORS adicionales.

### 4) Scripts de Machine Learning

Ejecuta desde la raíz o carpeta `ml-training` (activa el entorno si dependes de paquetes ML):

```powershell
# Preparación de datos
python ml-training/data_preparation.py

# Entrenamiento
python ml-training/train_model.py

# Evaluación
python ml-training/evaluate_model.py
```

Los artefactos de modelos deben guardarse en una carpeta dedicada (por ejemplo, `ml-training/models/`) y no se recomienda versionarlos si son pesados.

## API y documentación
- Swagger/OpenAPI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`
- Endpoints típicos (pueden variar según tu implementación):
  - `POST /triage/assess` – Clasifica el nivel de triage de un paciente.
  - `POST /tiss28/calc` – Calcula el puntaje TISS-28.
  - `GET /patients` – Lista de pacientes.
  - `WebSocket /ws` – Canal para eventos en tiempo real.

## Pruebas
- **Backend**: `pytest`
- **Frontend**: `npm test`

## Buenas prácticas y seguridad
- No subir archivos `.env` ni credenciales.
- Mantener los modelos y datasets grandes fuera del repositorio.
- Configurar CORS únicamente para orígenes seguros en producción.
- Usar HTTPS y secretos robustos en despliegues reales.

## Problemas comunes
- "Frontend como submódulo": si ves el mensaje de Git sobre repositorio embebido, elimina `frontend/.git` y vuelve a agregar los archivos.
- "Código dentro de venv": mueve el código a `backend/app` y mantén `venv` solo para paquetes.
- CRLF/LF en Windows: Git puede advertir sobre saltos de línea; no suele afectar la ejecución.

---

¿Necesitas ayuda para desplegar en producción (Docker, CI/CD, hosting)? Podemos añadir una guía de despliegue y un `docker-compose.yml` en pasos siguientes.