"""Database bootstrap (blueprint 12, storage/database.py).

Schema ownership belongs to Alembic migrations; init_database never creates or
rebuilds tables implicitly (blueprint 06, section 11).
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


def init_database(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    """Create the engine and a session factory for the given URL."""
    engine = create_engine(database_url)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)
