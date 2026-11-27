"""Job handlers, looked up by the job's `type`.

A handler takes the job's `payload` and returns its `result` (both JSON-able
dicts). It signals failure by raising `TransientJobError` or
`PermanentJobError` (app/jobs/errors.py); any other exception counts as
transient. Delivery is at least once, so a handler may run more than once for
the same job (e.g. after a worker crash): keep handlers idempotent.
"""

from collections.abc import Callable
from typing import Any

from app.jobs.errors import PermanentJobError, TransientJobError

Handler = Callable[[dict[str, Any]], dict[str, Any]]

_FAILURES: dict[str, type[Exception]] = {
    "transient": TransientJobError,
    "permanent": PermanentJobError,
}


def echo(payload: dict[str, Any]) -> dict[str, Any]:
    """`diagnostic.echo`: return `{"message": payload["message"]}`.

    `payload["fail"]` (optional) makes it fail on purpose, to exercise retries
    and dead-lettering: `"transient"` raises `TransientJobError`, `"permanent"`
    raises `PermanentJobError`. The API has already validated the payload
    (`EchoPayload`), and `fail` is absent when not set.
    """
    fail = payload.get("fail")
    if error_type := _FAILURES.get(fail):
        raise error_type(f"echo: asked to fail ({fail})")

    return {"message": payload["message"]}


# The registry the worker gets. A new job type = a handler + a line here (and,
# if clients may submit it, a variant in app/api/schemas/job.py `JobCreate`).
HANDLERS: dict[str, Handler] = {
    "diagnostic.echo": echo,
}
