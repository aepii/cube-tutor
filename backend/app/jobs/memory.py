"""In-process `JobQueue` with Service Bus peek-lock semantics (see app/jobs/queue.py).

Used by the tests and, until 24c, by the API. Lives in one process only.
"""

import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from uuid import UUID, uuid4

from app.jobs.queue import (
    MAX_DELIVERY_COUNT_EXCEEDED,
    JobMessage,
    LockLostError,
    ReceivedMessage,
)


@dataclass
class _Entry:
    message: JobMessage
    delivery_count: int = 0
    dead_letter_reason: str | None = None


class InMemoryJobQueue:
    """Peek-lock queue held in memory.

    - `lock_duration`: seconds a received message stays locked.
    - `max_delivery_count`: deliveries before the message is dead-lettered.
    - `clock`: monotonic seconds; tests pass a fake clock and never sleep.

    Lock expiry is checked on every call against `clock()` (no timer thread).
    `receive` never blocks: with nothing visible it returns None at once.
    Must be thread-safe: the API sends from FastAPI's threadpool.
    """

    def __init__(
        self,
        lock_duration: float = 30.0,
        max_delivery_count: int = 10,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._lock_duration = lock_duration
        self._max_delivery_count = max_delivery_count
        self._clock = clock

        self._lock = Lock()

        self._visible: deque[_Entry] = deque()
        self._locked: dict[UUID, tuple[_Entry, float]] = {}

        self._dlq_visible: deque[_Entry] = deque()
        self._dlq_locked: dict[UUID, tuple[_Entry, float]] = {}

    def send(self, message: JobMessage) -> None:
        with self._lock:
            entry = _Entry(message=message)
            self._visible.append(entry)

    def receive(self, max_wait: float = 0) -> ReceivedMessage | None:
        with self._lock:
            self._release_expired()
            return self._deliver(self._visible, self._locked)

    def complete(self, msg: ReceivedMessage) -> None:
        with self._lock:
            self._release_expired()
            self._pop_lock(msg)

    def abandon(self, msg: ReceivedMessage) -> None:
        with self._lock:
            self._release_expired()
            entry = self._pop_lock(msg)
            self._release(entry)

    def dead_letter(self, msg: ReceivedMessage, reason: str) -> None:
        with self._lock:
            self._release_expired()
            entry = self._pop_lock(msg)
            # A message received from the DLQ keeps its first reason: that's
            # what the drain (24b) records on the job.
            if entry.dead_letter_reason is None:
                entry.dead_letter_reason = reason
            self._dlq_visible.append(entry)

    def renew_lock(self, msg: ReceivedMessage) -> None:
        with self._lock:
            self._release_expired()
            locked = self._lock_table(msg)
            entry, _ = locked[msg.lock_token]
            locked_until = self._clock() + self._lock_duration
            locked[msg.lock_token] = (entry, locked_until)
            msg.locked_until = locked_until

    def receive_dead_lettered(self, max_wait: float = 0) -> ReceivedMessage | None:
        with self._lock:
            self._release_expired()
            return self._deliver(self._dlq_visible, self._dlq_locked)

    # --- private: callers hold self._lock ----------------------------------

    def _deliver(
        self, source: deque[_Entry], locked: dict[UUID, tuple[_Entry, float]]
    ) -> ReceivedMessage | None:
        """Lock the next entry of `source` into `locked` and hand it out."""
        if not source:
            return None

        entry = source.popleft()
        entry.delivery_count += 1
        lock_token = uuid4()
        locked_until = self._clock() + self._lock_duration
        locked[lock_token] = (entry, locked_until)

        return ReceivedMessage(
            message=entry.message,
            lock_token=lock_token,
            delivery_count=entry.delivery_count,
            locked_until=locked_until,
            dead_letter_reason=entry.dead_letter_reason,
        )

    def _lock_table(self, msg: ReceivedMessage) -> dict[UUID, tuple[_Entry, float]]:
        """The dict that holds this delivery's lock, or LockLostError."""
        for locked in (self._locked, self._dlq_locked):
            if msg.lock_token in locked:
                return locked
        raise LockLostError(
            f"lock {msg.lock_token} for job {msg.message.job_id} "
            "expired or was already settled"
        )

    def _pop_lock(self, msg: ReceivedMessage) -> _Entry:
        entry, _ = self._lock_table(msg).pop(msg.lock_token)
        return entry

    def _release_expired(self) -> None:
        now = self._clock()
        for locked in (self._locked, self._dlq_locked):
            for lock_token, (entry, locked_until) in list(locked.items()):
                if locked_until <= now:
                    del locked[lock_token]
                    self._release(entry)

    def _release(self, entry: _Entry) -> None:
        if entry.dead_letter_reason is not None:
            self._dlq_visible.append(entry)
        elif entry.delivery_count >= self._max_delivery_count:
            entry.dead_letter_reason = MAX_DELIVERY_COUNT_EXCEEDED
            self._dlq_visible.append(entry)
        else:
            self._visible.append(entry)
