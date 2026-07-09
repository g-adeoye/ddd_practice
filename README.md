# Async Job Queue with Backpressure & Priority Scheduling
---
A production-grade async job queue demonstrating backpressure, weighted fair scheduling, crash recovery, and dead letter queue patterns.

## What this demonstrates
---
This project implements the mechanics that services like SQS hide behind abstractions: Redis Streams consumer groups for at-least-once delivery, a two-watermark backpressure band to prevent queue overflow, weighted fair scheduling to prevent priortiy starvation and a visibility timeout reaper for crash recovery.

## Architecture 
---

```
Client → POST /jobs → Backpressure check → PostgreSQL (job state)
                                         → Redis Streams (3 priority queues)

Worker → Weighted scheduler (60/30/10) → XREADGROUP → Execute + heartbeat
       → Success: XACK + COMPLETED
       → Retryable failure: exponential backoff + re-enqueue
       → Permanent failure: Dead Letter Queue

Reaper (10s) → Per-priority visibility timeouts → Re-enqueue crashed workers
             → Zombie detection (stale heartbeat > 60s)
```