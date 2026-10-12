"""Entorno de Alembic. La URL de la BD sale de app.core.config (DATABASE_URL)
y el esquema objetivo de los modelos SQLAlchemy, igual que en la app."""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.models.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Al ejecutarse desde la app (lifespan) no reconfiguramos el logging, para no
# desactivar los loggers de uvicorn.
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _configure_kwargs() -> dict:
    # render_as_batch permite que futuras migraciones alteren columnas y
    # constraints en SQLite (que no soporta ALTER TABLE completo).
    return {"target_metadata": target_metadata, "render_as_batch": True}


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_configure_kwargs(),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = config.attributes.get("connection")
    if connectable is not None:
        context.configure(connection=connectable, **_configure_kwargs())
        with context.begin_transaction():
            context.run_migrations()
        return

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, **_configure_kwargs())
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
