import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator


class JobCreate(BaseModel):
    "Request body for POST /jobs."

    payload: dict[str, Any]
    priority: Literal["NORMAL", "HIGH", "CRITICAL"] = "NORMAL"
    max_retries: int = 5
    
    @field_validator("priority", mode="before")
    def to_upper(cls, v):
        return v.upper() if isinstance(v, str) else v


class JobResponse(BaseModel):
    "Response body for job endpoints."

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    priority: str
    payload: dict[str, Any]
    result: dict[str, Any] | None
    retry_count: int
    error: str | None
    created_at: datetime
    updated_at: datetime


class QueueDepthResponse(BaseModel):
    depths: dict[str, int]
    total: int
    high_watermark: int
    low_watermark: int
    accepting_jobs: bool
    dlq_depth: int
    backpressure_active: bool


class WeightUpdateRequest(BaseModel):
    "Request body for PATCH /queues/weights."

    critical: int
    high: int
    normal: int

    @field_validator("critical", "high", "normal")
    def must_be_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Weight must be non-negative")
        return v

    def model_post_init(self, __context: Any) -> None:
        total = self.critical + self.high + self.normal
        if total != 100:
            raise ValueError(f"Weights must sum to 100, got {total}")


class WeightResponse(BaseModel):
    "Response body for weight endpoints."

    critical: int
    high: int
    normal: int
    source: str  # "redis" or "config" - tells caller where values came from
