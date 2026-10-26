"""Configuracion de la aplicacion via variables de entorno (o backend/.env).

pydantic-settings valida los tipos al arrancar: un valor invalido (por
ejemplo CHAT_SESSION_TTL_MINUTES=abc) falla con un error claro en lugar de
propagarse en tiempo de ejecucion.
"""
import logging
import secrets
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

    # Clave para firmar los JWT del personal. Si no se define se genera una
    # aleatoria al arrancar: funciona, pero las sesiones se invalidan en cada
    # reinicio y no sirve con varios workers. En produccion, definirla.
    SECRET_KEY: str = Field(default="", validate_default=True)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=480, gt=0)

    @field_validator("SECRET_KEY")
    @classmethod
    def _default_secret_key(cls, value: str) -> str:
        if value:
            return value
        logging.getLogger(__name__).warning(
            "SECRET_KEY no definida: se usa una clave aleatoria temporal; "
            "las sesiones del personal se perderan al reiniciar el backend."
        )
        return secrets.token_urlsafe(32)

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
