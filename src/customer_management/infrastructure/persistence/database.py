from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


DATABASE_URL_ENVIRONMENT_VARIABLE = "DATABASE_URL"


def database_url_from_environment() -> str:
    database_url = os.environ.get(DATABASE_URL_ENVIRONMENT_VARIABLE)
    if not database_url:
        raise RuntimeError(
            f"{DATABASE_URL_ENVIRONMENT_VARIABLE} environment variable is required."
        )
    return database_url


def create_database_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)

