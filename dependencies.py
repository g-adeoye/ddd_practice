from typing import Annotated, cast

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db

SettingsDep = Annotated[Settings, Depends(get_settings)]

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_redis(request: Request) -> Redis:
    """
    Pull the Redis client from FastAPU app state.
    The client is attached to app.state.redis in the lifespan function.
    """
    return cast(Redis, request.app.state.redis)


RedisDep = Annotated[Redis, Depends(get_redis)]
