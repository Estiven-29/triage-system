"""Configuracion de la aplicacion via variables de entorno."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "Sistema de Triage Inteligente API"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./triage.db")

    ALLOWED_ORIGINS: list[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000"
    ).split(",")


settings = Settings()
