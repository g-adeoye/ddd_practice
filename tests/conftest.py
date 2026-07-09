import pytest
from collections.abc import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from app.config import get_settings
from infrastructure.redis_client import create_redis_client, close_redis_client
from httpx import ASGITransport, AsyncClient
from main import app
from app.database import get_db
from redis.asyncio import Redis

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
    
@pytest.fixture(autouse=True, scope="function")
async def reset_database(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    "Truncate tables before each test."
    async with engine.begin() as conn:
        tables = ", ".join(SQLModel.metadata.tables.keys())
        if tables:
            query = f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"
            await conn.execute(text(query))
    yield
    
@pytest.fixture(autouse=True, scope="function")
async def flush_redis(redis_client: Redis) -> AsyncGenerator[None, None]:
    "flush redis before each test."
    await redis_client.flushdb()
    yield

@pytest.fixture(scope="session")
async def redis_client() -> AsyncGenerator[Redis, None]:
    "One redis client for the entire test session"
    client = await create_redis_client()
    yield client
    await close_redis_client(client)


@pytest.fixture
async def db(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    "Fresh db session per test"
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def redis(redis_client: Redis) -> Redis:
    "Alias so tests recieve 'redis' as a fixture name."
    return redis_client


@pytest.fixture
async def client(db: AsyncSession, redis: Redis) -> AsyncGenerator[AsyncClient, None]:
    """
    Test HTTP client with DB and Redis injected.
    Overrides FastAPI's dependency system for the duration of each test.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.state.redis = redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

    app.dependency_overrides.clear()
