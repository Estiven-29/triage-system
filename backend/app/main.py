"""Aplicacion principal FastAPI - Sistema de Triage Inteligente."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import chatbot, dashboard, triage, websocket
from .core.config import settings
from .db.database import engine
from .models.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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
