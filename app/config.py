from functools import lru_cache
from dataclasses import dataclass


@dataclass
class Settings:
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = (
        "postgresql+asyncpg://queue_worker:queue_password@localhost:5432/queue_db"
    )
    high_watermark: int = 10000
    low_watermark: int = 2000
    weight_critical: int = 60
    weight_high: int = 30
    weight_normal: int = 10
    max_retries: int = 5
    job_timeout_seconds: int = 30
    app_env: str = "development"
    worker_count: int = 4


@lru_cache
def get_settings() -> Settings:
    return Settings()
