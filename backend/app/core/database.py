"""Database utilities for the analytics service."""
from __future__ import annotations

from typing import Callable, Tuple

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


def _sqlite_connect_args(database_url: str) -> dict:
    return {"check_same_thread": False} if database_url.startswith("sqlite") else {}


def create_session_factory(database_url: str) -> Tuple[Engine, Callable[[], Session]]:
    """Create an engine and session factory for the provided database URL."""

    engine = create_engine(database_url, connect_args=_sqlite_connect_args(database_url), future=True)
    session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

    def _session_factory() -> Session:
        return session_local()

    return engine, _session_factory
