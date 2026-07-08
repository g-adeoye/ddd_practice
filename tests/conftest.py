import pytest
from collections.abc import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from app.config import get_settings

get_settings.cache_clear()
settings = get_settings()

@pytest.fixture
def queue_weights() -> dict[str, int]:
    return {"critical": 60, "high": 30, "normal": 10}

@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    "One engine for the entire test session."

    eng = create_async_engine(settings.database_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()
