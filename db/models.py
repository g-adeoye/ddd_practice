from sqlmodel import Field, SQLModel, Column, JSON, func
from sqlalchemy import Enum
from uuid import uuid4, UUID
from domain.models import JobState, JobPriority
from datetime import datetime


class JobModel(SQLModel, table=True):
    __tablename__: str = "job"
    id: UUID = Field(default=uuid4, primary_key=True)
    status: JobState = Field(sa_column=Column(Enum(JobState, native_enum=True)))
    priority: JobPriority = Field(sa_column=Column(Enum(JobPriority, native_enum=True)))
    payload: dict | None = Field(default={}, sa_column=Column(JSON))
    result: dict | None = Field(sa_column=Column(JSON), default={})
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=5)
    worker_id: str | None
    heartbeat_at: datetime | None
    error: str | None
    created_at: datetime = Field(default=func.now())
    updated_at: datetime = Field(
        default=func.now(), sa_column_kwargs={"onupdate": func.now()}
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} status={self.status} priority={self.priority}>"
