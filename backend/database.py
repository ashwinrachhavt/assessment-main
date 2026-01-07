from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base


def get_async_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")


Base = declarative_base()

engine = None
SessionLocal = None


def init_engine(async_url: str | None = None) -> None:
    """
    Initialize the global async SQLAlchemy engine/sessionmaker.

    Tests can call this to point the app at a temporary DB without reloading modules.
    """
    global engine, SessionLocal
    engine = create_async_engine(async_url or get_async_url(), pool_pre_ping=True)
    SessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )


init_engine()
