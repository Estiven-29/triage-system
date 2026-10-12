"""Configuracion de la aplicacion via variables de entorno (o backend/.env).

pydantic-settings valida los tipos al arrancar: un valor invalido (por
ejemplo CHAT_SESSION_TTL_MINUTES=abc) falla con un error claro en lugar de
propagarse en tiempo de ejecucion.
"""
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Sistema de Triage Inteligente API"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = "sqlite:///./triage.db"

    # Lista separada por comas, p. ej. "http://localhost:3000,https://mi.app".
    # NoDecode evita que pydantic-settings la intente leer como JSON.
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Minutos de inactividad tras los cuales una sesion de chatbot expira.
    CHAT_SESSION_TTL_MINUTES: int = Field(default=120, gt=0)

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, url: str) -> str:
        """Fija explicitamente el driver psycopg (v3) para Postgres. SQLAlchemy
        2.0 usa psycopg2 por defecto con "postgresql://" y 2.1 usa psycopg,
        asi que sin esto el driver dependeria de la version instalada."""
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
