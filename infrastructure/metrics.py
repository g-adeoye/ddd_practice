"""
Prometheus metrics for the Async Job Queue

All metrics are defined here once and imported where needed.
This avoids duplicate registration errors from multiple imports.

Metrics specified:
    - queue depth                   Gauge - current depth per priority stream
    - jobs_processed_total          Counter - jobs completed or failed
    - backpressure_rejection_total  Counter - times 503 was returned
    - zombie_jobs_reaped_total      Counter - jobs recovered by reaper.
"""

from prometheus_client import Counter, Gauge

queue_depth = Gauge(
    "queue_depth",
    "Current number of messages in each priority stream",
    labelnames=["priority"],
)

jobs_processed_total = Counter(
    "jobs_processed_total",
    "Total number of jobs processed by workers",
    labelnames=["status"],  # completed | failed
)

backpressure_rejection_total = Counter(
    "backpressure_rejection_total",
    "Total number of job submissions rejected due to backpressure (503)",
)

zombie_jobs_reaped_total = Counter(
    "zombie_jobs_reaped_total",
    "Total zombie jobs detected via stale heartbeat and marked FAILED",
)

# Force registriation so they appear with 0.0 values even if not yet triggered
queue_depth.labels(priority="crititcal").set(0)
queue_depth.labels(priority="high").set(0)
queue_depth.labels(priority="normal").set(0)

jobs_processed_total.labels(status="completed").inc(0)
jobs_processed_total.labels(status="failed").inc(0)

backpressure_rejection_total.inc(0)
zombie_jobs_reaped_total.inc(0)
