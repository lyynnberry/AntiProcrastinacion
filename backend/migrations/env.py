from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.core.config import settings
from app.db.base import Base
from app.db import registro_modelos  # noqa: F401  (registra todos los modelos)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _url() -> str:
    # Las pruebas inyectan su propia URL con set_main_option("sqlalchemy.url", ...).
    return config.get_main_option("sqlalchemy.url") or settings.database_url


def run_migrations_online() -> None:
    engine = create_engine(_url())
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
