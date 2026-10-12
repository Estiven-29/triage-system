from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.db.migrations import ALEMBIC_INI
from app.models.models import Base


def _config(connection) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.attributes["configure_logger"] = False
    config.attributes["connection"] = connection
    return config


def test_migrations_match_models(tmp_path):
    # Si alguien cambia un modelo sin crear la migracion correspondiente
    # (alembic revision --autogenerate), este test falla.
    engine = create_engine(f"sqlite:///{tmp_path / 'm.db'}")
    with engine.begin() as connection:
        command.upgrade(_config(connection), "head")
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == []


def test_downgrade_removes_all_tables(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'm.db'}")
    with engine.begin() as connection:
        command.upgrade(_config(connection), "head")
        command.downgrade(_config(connection), "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
