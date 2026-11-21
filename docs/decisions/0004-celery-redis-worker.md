# 0004 — Celery + Redis for background work

**Status:** in the code today (placeholder task only), **planned to be superseded**. [`ROADMAP.md`](../../ROADMAP.md) §3.9, §3.10 and Phase 24 replace Celery + self-hosted Redis with an Azure Service Bus queue, a `Job` table and a direct `azure-servicebus` consumer. Not built yet. Write a new ADR when that lands, and mark this one superseded.

**Evidence:** commit `bf3d73c` (2026-01-29) "Setup Celery + Redis and a mock using a FastAPI endpoint". ROADMAP §5 states the intended use (the scan pipeline, **not built**) and the tradeoff. Current code in [data-pipeline.md](../data-pipeline.md#celery-tasks).

## Context
The planned feature is photographing a physical cube → detecting its state with OpenCV → solving. Image processing is too slow and heavy for a request/response handler. Today the only producer is `POST /v1/images/upload`, which enqueues a fake `process_image` task.

## Decision
A Celery worker in its own container with Redis as broker (db 0) and result backend (db 1). Originally the task code lived in a repo-root `shared/` folder bind-mounted into separate API and worker containers. Since 4c it lives in [`backend/app/worker/`](../../backend/app/worker/) and the worker runs from the backend image ([0005](0005-one-python-package-uv.md)).

Stated in ROADMAP §5 (plans, not implemented; they carry over to the Service Bus design):
- Only an id goes through the queue, never the image bytes.
- Postgres is the source of truth for job status, not a queue result backend.

## Alternatives
- **FastAPI `BackgroundTasks`.** Not discussed. *Inferred:* runs in the API process, with no retries, isolation or separate scaling.
- **On-device color classification.** ROADMAP §5 says plainly that this could run on-device and that the queue is justified as async/heavy processing *and* as an async-architecture showcase.
- **RQ / Dramatiq / arq.** Not discussed in the repo.
- **Azure Service Bus + a direct consumer.** This is the *planned replacement* (ROADMAP §3.10). Stated reasons: Celery's Azure transports are community-maintained and lag behind its Redis and RabbitMQ ones, and a direct consumer shows peek-lock, dead-lettering and redelivery first-hand.

## Consequences
- \+ Heavy work stays out of the API and can be retried and scaled separately.
- − An extra container and dependency (Redis) for what is a placeholder task today.
- − ~~Code sharing through a bind mount instead of an installed package.~~ Fixed in 4c by [0005](0005-one-python-package-uv.md): one package and one image, so the worker also has the models.
- − The result backend is configured but nothing reads it, and the API has no status endpoint.
