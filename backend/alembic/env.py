from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure project root is on sys.path so `app` is importable when running Alembic
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.config import settings
from app.db.base import SQLModel
from app.models import user  # noqa: F401

config = context.config
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        # If logging config sections are missing, skip configuring logging
        pass

target_metadata = SQLModel.metadata

def _get_config_section():
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = settings.DATABASE_URL
    return section

def run_migrations_offline() -> None:
    context.configure(url=settings.DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(_get_config_section(), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
