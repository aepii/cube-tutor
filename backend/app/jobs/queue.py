"""The job queue contract (ROADMAP §3.10, ADR 0008).

Mirrors Azure Service Bus in peek-lock mode, so the worker (24b) runs the same
against `InMemoryJobQueue` (tests, local) and `ServiceBusJobQueue` (24c):

- `receive` locks a message for `lock_duration` and returns it; it stays
  invisible to other receivers until it's settled or the lock expires.
- Settle a received message with exactly one of `complete`, `abandon` or
  `dead_letter`. Settling after the lock expired (or twice) raises
  `LockLostError`.
- Every delivery adds 1 to `delivery_count`. A message that's abandoned, or
  whose lock expires, with `delivery_count >= max_delivery_count` goes to the
  dead-letter queue with reason `MaxDeliveryCountExceeded` instead of being
  redelivered.
- The dead-letter queue is read the same way (`receive_dead_lettered`, then
  `complete`). A message there never returns to the main queue, and
  dead-lettering it again keeps its first reason.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

MAX_DELIVERY_COUNT_EXCEEDED = "MaxDeliveryCountExceeded"


class LockLostError(Exception):
    """The message's lock expired, or it was already settled."""


@dataclass(frozen=True)
class JobMessage:
    """What goes on the queue: only the id and type. The row holds the rest."""

    job_id: UUID
    type: str


@dataclass
class ReceivedMessage:
    """One delivery of a message, locked for the receiver until `locked_until`.

    `lock_token` identifies this delivery: a redelivery of the same message gets
    a new token, so an old `ReceivedMessage` can't settle it.
    """

    message: JobMessage
    lock_token: UUID
    delivery_count: int
    locked_until: float  # on the queue's clock (seconds)
    dead_letter_reason: str | None = None  # set only on dead-lettered messages


class JobQueue(Protocol):
    def send(self, message: JobMessage) -> None: ...

    def receive(self, max_wait: float = 0) -> ReceivedMessage | None:
        """Lock and return the next visible message, or None if there is none
        within `max_wait` seconds."""
        ...

    def complete(self, msg: ReceivedMessage) -> None:
        """Remove the message for good (success, or a duplicate)."""
        ...

    def abandon(self, msg: ReceivedMessage) -> None:
        """Release the lock so the message is redelivered (transient error)."""
        ...

    def dead_letter(self, msg: ReceivedMessage, reason: str) -> None:
        """Move the message to the dead-letter queue (permanent error)."""
        ...

    def renew_lock(self, msg: ReceivedMessage) -> None:
        """Extend the lock by `lock_duration` from now; updates `msg.locked_until`."""
        ...

    def receive_dead_lettered(self, max_wait: float = 0) -> ReceivedMessage | None:
        """Lock and return the next dead-lettered message (reason set), or None."""
        ...
