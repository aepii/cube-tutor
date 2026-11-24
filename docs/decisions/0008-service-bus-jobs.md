# 0008: Background jobs: a `Job` table plus a direct Azure Service Bus consumer

**Status:** accepted (24a, issue #54). Supersedes [ADR 0004](0004-celery-redis-worker.md) (Celery + Redis, already removed in #39). Builds on [ADR 0007](0007-azure-container-apps-bicep.md) (Container Apps, managed identities).

**Evidence:** ROADMAP §3.9, §3.10 (stated), Phase 24; issues #54 (24a), #55 (24b).

## Context
- Two planned features don't fit in a request/response cycle: the CFOP solver (Phase 15, a search that can take seconds) and the scan pipeline (Phase 8, image processing). Clients need a status to poll, retries for transient failures, and a place where poison work stops.
- The platform is Azure Container Apps ([0007](0007-azure-container-apps-bicep.md)), where a worker can scale from 0 on queue length (KEDA).
- It's a portfolio project: the queue semantics (at-least-once delivery, locks, dead-lettering) should be visible in our code, not hidden in a framework.

## Decision
- **A `job` table is the source of truth** for status, payload, result, error and attempts. Clients poll `GET /v1/jobs/{id}` (owner only). Postgres, not the queue, answers "what happened to my job".
- **The queue carries only `{job_id, type}`** (never payloads or blobs).
- **Azure Service Bus** (Basic tier, one `jobs` queue) in **peek-lock** mode, consumed directly with the `azure-servicebus` SDK by a worker that runs from the backend image ([0005](0005-one-python-package-uv.md)).
- **A `JobQueue` protocol** ([`app/jobs/queue.py`](../../backend/app/jobs/queue.py)) with two implementations: `InMemoryJobQueue` (24a, with the same lock, delivery-count and dead-letter rules, driven by an injectable clock) and `ServiceBusJobQueue` (24c). pytest needs neither Azure nor the emulator.
- **Enqueue commits the row, then sends.** If the send fails, the request still succeeds and the job stays `pending`; a **sweeper** re-sends `pending` jobs older than a threshold. The fully correct version is a **transactional outbox** (write the message to an outbox table in the same transaction, then relay it). It isn't worth a relay process at this size; the sweeper gives the same eventual outcome because the worker is idempotent.
- **The worker** (24b) is idempotent on `job_id` (Service Bus delivers at least once), renews its lock during long work, completes on success, abandons on a transient error (retried up to the queue's max delivery count), and dead-letters on a permanent one. A dead-letter drain marks those jobs `failed`.

## Alternatives
- **Celery** (the previous choice, [0004](0004-celery-redis-worker.md)). Mature, with retries and scheduling built in. But its Azure Service Bus transport (kombu) is community-maintained and lags behind Redis/RabbitMQ, so on Azure it would mean running Redis or RabbitMQ ourselves. It also hides the delivery semantics this project wants to show.
- **Azure Functions** with a Service Bus trigger. Less code and built-in scaling, but a second hosting model and runtime next to Container Apps, a different local dev story, and the models/engine would have to be packaged twice. KEDA on Container Apps gives the same scale-to-zero from the image we already ship.
- **Azure Storage Queues.** Cheaper and simpler, but no dead-letter queue, no max delivery count, and no duplicate detection: we'd rebuild those by hand. Service Bus Basic costs cents at this volume.
- **FastAPI `BackgroundTasks`.** Runs in the API process: no retries, lost on restart, and scales with the API instead of the work.

## Consequences
- \+ Job status survives queue loss and redelivery; the API and worker scale separately; the worker scales to zero.
- \+ The same tests run against the in-memory queue, and the emulator test (24c) checks the real SDK with the same contract.
- − At-least-once delivery means handlers must be idempotent, and a crash mid-job reruns it.
- − Commit-then-send has a window where a job waits for the sweeper; an outbox would close it.
- − Until 24c the API's queue is in-process and nothing consumes it, so jobs posted to a running API stay `pending`.
