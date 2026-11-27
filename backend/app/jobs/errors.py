"""How a handler tells the worker what went wrong, and the dead-letter reasons.

- `TransientJobError`: worth retrying (a timeout, a busy dependency). The worker
  abandons the message; the queue redelivers it until `max_delivery_count`,
  then dead-letters it with `MaxDeliveryCountExceeded`.
- `PermanentJobError`: retrying won't help (bad input). The worker marks the
  job `failed` and dead-letters the message at once.
- Any other exception counts as transient.
"""


class TransientJobError(Exception):
    """Retry this job (the message is abandoned and redelivered)."""


class PermanentJobError(Exception):
    """Don't retry this job (it's marked failed and dead-lettered)."""


# Reasons the worker passes to `JobQueue.dead_letter`. The queue's own reason,
# `MaxDeliveryCountExceeded`, lives in app/jobs/queue.py.
JOB_NOT_FOUND = "JobNotFound"
UNKNOWN_JOB_TYPE = "UnknownJobType"
PERMANENT_ERROR = "PermanentJobError"
