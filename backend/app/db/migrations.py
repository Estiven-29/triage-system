"""Aplica las migraciones de Alembic desde codigo (arranque de la app,
init_db.py y tests), sin depender de que el CLI se ejecute aparte."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from .database import engine

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


class LegacyDatabaseError(RuntimeError):
    """La BD tiene tablas pero no esta versionada con Alembic."""


def _alembic_config() -> Config:
    config = Config(str(ALEMBIC_INI))
    config.attributes["configure_logger"] = False
    return config


def run_migrations() -> None:
    tables = set(inspect(engine).get_table_names())
    if tables and "alembic_version" not in tables:
        # BD creada con el antiguo Base.metadata.create_all. Alembic fallaria
        # con un "table already exists" poco claro, asi que lo explicamos.
        raise LegacyDatabaseError(
            "La base de datos se creo antes de usar migraciones (Alembic). "
            "Si es una BD de desarrollo, borrala y vuelve a arrancar. Si ya "
            "tiene el esquema actual, marcala con: alembic stamp head"
        )
    command.upgrade(_alembic_config(), "head")
