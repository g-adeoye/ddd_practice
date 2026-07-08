from collections.abc import AsyncGenerator
from fastapi import FastAPI
from .config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",  # logs SQL only in dev
    pool_pre_ping=True,  # validates connections before use
)


AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keeps model attributes accessible after commit
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    "FastAPI dependency - yields a database session per request."
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
