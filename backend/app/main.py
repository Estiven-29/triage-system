"""Aplicacion principal FastAPI - Sistema de Triage Inteligente."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, chatbot, dashboard, triage, websocket
from .core.config import settings
from .db.migrations import run_migrations
from .ml.classifier import load_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    # Cargamos (o entrenamos, si no existe) el modelo al arrancar para que
    # la primera peticion de clasificacion no pague ese costo.
    load_model()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API de apoyo a la clasificacion de pacientes en urgencias. "
        "Proyecto educativo/portafolio: no es un dispositivo medico ni "
        "debe usarse para decisiones clinicas reales."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chatbot.router)
app.include_router(triage.router)
app.include_router(dashboard.router)
app.include_router(websocket.router)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
