"""Configuracion de la aplicacion via variables de entorno."""
import os

from dotenv import load_dotenv

load_dotenv()


def _normalize_database_url(url: str) -> str:
    """Fija explicitamente el driver psycopg (v3) para Postgres. SQLAlchemy
    2.0 usa psycopg2 por defecto con "postgresql://" y 2.1 usa psycopg, asi
    que sin esto el driver dependeria de la version instalada."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class Settings:
    APP_NAME: str = "Sistema de Triage Inteligente API"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = _normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite:///./triage.db")
    )

    ALLOWED_ORIGINS: list[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")

    # Minutos de inactividad tras los cuales una sesion de chatbot expira.
    CHAT_SESSION_TTL_MINUTES: int = int(os.getenv("CHAT_SESSION_TTL_MINUTES", "120"))


settings = Settings()
