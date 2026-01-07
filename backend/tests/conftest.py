from __future__ import annotations

import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import database
import main
from models import Base


@pytest.fixture
async def _test_db(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    database.init_engine(f"sqlite+aiosqlite:///{db_path.as_posix()}")

    assert database.engine is not None
    async with database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await database.engine.dispose()


@pytest.fixture
async def client(_test_db: None) -> AsyncClient:
    transport = ASGITransport(app=main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
