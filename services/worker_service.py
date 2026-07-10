import uuid
import random
import asyncio
from services import job_service
from app.config import get_settings
from services.queue_service import QueueMessage
from services import queue_service, job_service
from infrastructure.metrics import jobs_processed_total

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis


async def _heartbeat_loop(
    db: AsyncSession, job_id: uuid.UUID, interval_secs: int = 5
) -> None:
    "Writes a heartbeat every 'interval_secs' while a job runs."
    while True:
        await asyncio.sleep(interval_secs)
        await job_service.update_heartbeat(db, job_id)
        await db.commit()


def _backoff_seconds(
    retry_count: int, base: float = 1.0, max_delay: float = 60.0
) -> float:
    """
    Exponential backoff with full jitter.

    Formula: min(base * 2^retry_count, max_delay) * random(0, 1)
    Why jitter ? Without it, all failed jobs retry at the same moment,
    creating a thundering herd that hammers the downstream service again.
    Jitter spreads the retries across the backoff window.

    retry_count=0 -> 0-1s, 1 -> 0-2s, 2 -> 0-4s, 3 -> 0-8s, 4 -> 0-16s
    """

    delay = min(base * 2**retry_count, max_delay) * random.random()

    return float(delay)


async def _dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    "Route a job to the correct handler based on its 'type' field."
    job_type = payload.get("type", "unknown")

    if job_type == "send_email":
        await asyncio.sleep(0.1)
        return {"sent": True, "to": payload.get("to")}

    elif job_type == "generate_report":
        await asyncio.sleep(0.5)
        return {"report_id": str(uuid.uuid4())}

    else:
        raise ValueError(f"Unknown job type: {job_type!r}")


async def process_one(
    redis: Redis,
    db: AsyncSession,
    consumer_name: str,
) -> bool:
    """
    Pull one job from the queue and execute it.
    Returns True if a job was processed, False if the queue was empty.
    """
    settings = get_settings()
    message: QueueMessage | None = await queue_service.dequeue(redis, consumer_name)

    if message is None:
        return False

    job_id = uuid.UUID(message.job_id)

    await job_service.mark_running(db, job_id, worker_id=consumer_name)
    await db.commit()

    heartbeat_task = asyncio.create_task(_heartbeat_loop(db, job_id))

    try:
        # Execute with a hard timeout - prevents hung handlers from
        # blockin workers indefinitely. asyncio.TimeoutError is caught
        # below and treated as a regular job failure.
        result = await asyncio.wait_for(
            _dispatch(message.payload), timeout=settings.job_timeout_seconds
        )

        await queue_service.acknowledge(redis, message.stream, message.message_id)
        await job_service.mark_completed(db, job_id, result=result)
        await db.commit()

        jobs_processed_total.labels(status="completed").inc()

    except TimeoutError:
        job = await job_service.get_job(db, job_id)
        retry_count = (job.retry_count if job else 0) + 1
        max_retries = job.max_retries if job else settings.max_retries

        error_msg = f"Job timed out after {settings.job_timeout_seconds}"
        await job_service.mark_failed(
            db, job_id, error=error_msg, retry_count=retry_count
        )
        await db.commit()

        jobs_processed_total.labels(status="failed").inc()

        if retry_count >= max_retries:
            await queue_service.enqueue_dlq(
                redis,
                job_id=str(job_id),
                payload=message.payload,
                priority=message.priority,
                error=error_msg,
                retry_count=retry_count,
            )
        else:
            delay = _backoff_seconds(retry_count)
            await asyncio.sleep(delay)
            await queue_service.enqueue(
                redis,
                job_id=str(job_id),
                payload=message.payload,
                priority=message.priority,
            )

        await queue_service.acknowledge(redis, message.stream, message.message_id)

    except Exception as e:
        job = await job_service.get_job(db, job_id)
        retry_count = (job.retry_count if job else 0) + 1
        max_retries = job.max_retries if job else settings.max_retries

        error_msg = f"Job timed out after {settings.job_timeout_seconds}"
        await job_service.mark_failed(
            db, job_id, error=error_msg, retry_count=retry_count
        )
        await db.commit()

        jobs_processed_total.labels(status="failed").inc()

        if retry_count >= max_retries:
            await queue_service.enqueue_dlq(
                redis,
                job_id=str(job_id),
                payload=message.payload,
                priority=message.priority,
                error=error_msg,
                retry_count=retry_count,
            )
        else:
            delay = _backoff_seconds(retry_count)
            await asyncio.sleep(delay)
            await queue_service.enqueue(
                redis,
                job_id=str(job_id),
                payload=message.payload,
                priority=message.priority,
            )

        await queue_service.acknowledge(redis, message.stream, message.message_id)
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

    return True
