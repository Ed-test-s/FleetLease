from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import settings
from app.core.database import Base
from app.models import app_settings, chat, favorite, leasing, notification, reference, review, user, vehicle  # noqa: F401


def _alembic_config() -> Config:
    cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)
    return cfg


def _is_fresh_database(sync_url: str) -> bool:
    engine = create_engine(sync_url, future=True)
    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())
            return len(tables) == 0
    finally:
        engine.dispose()


def _create_schema_and_stamp_head(sync_url: str) -> None:
    engine = create_engine(sync_url, future=True)
    try:
        Base.metadata.create_all(bind=engine)
    finally:
        engine.dispose()
    command.stamp(_alembic_config(), "head")


def main() -> None:
    sync_url = settings.DATABASE_URL_SYNC
    if _is_fresh_database(sync_url):
        print("Database is empty. Creating schema from metadata and stamping Alembic head...")
        _create_schema_and_stamp_head(sync_url)
    else:
        print("Database is not empty. Running Alembic migrations...")
        command.upgrade(_alembic_config(), "head")


if __name__ == "__main__":
    main()
