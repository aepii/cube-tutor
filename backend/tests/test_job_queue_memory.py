"""AC5: InMemoryJobQueue has Service Bus peek-lock semantics (app/jobs/queue.py).

No database and no sleeping: lock expiry is driven by a FakeClock.
"""

from uuid import uuid4

import pytest

from app.jobs.memory import InMemoryJobQueue
from app.jobs.queue import MAX_DELIVERY_COUNT_EXCEEDED, JobMessage, LockLostError
from tests.helpers import FakeClock

LOCK = 30.0
MAX_DELIVERIES = 3


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def queue(clock) -> InMemoryJobQueue:
    return InMemoryJobQueue(
        lock_duration=LOCK, max_delivery_count=MAX_DELIVERIES, clock=clock
    )


def _msg(type: str = "diagnostic.echo") -> JobMessage:
    return JobMessage(job_id=uuid4(), type=type)


# --- receive ---------------------------------------------------------------


def test_receive_on_empty_queue_returns_none(queue):
    assert queue.receive() is None


def test_receive_returns_messages_in_send_order(queue):
    a, b = _msg(), _msg()
    queue.send(a)
    queue.send(b)
    assert queue.receive().message == a
    assert queue.receive().message == b


def test_receive_locks_the_message_for_lock_duration(queue, clock):
    queue.send(_msg())
    got = queue.receive()
    assert got.delivery_count == 1
    assert got.locked_until == clock.now + LOCK
    assert got.dead_letter_reason is None


def test_a_received_message_is_invisible_while_locked(queue, clock):
    queue.send(_msg())
    queue.receive()
    clock.advance(LOCK - 1)
    assert queue.receive() is None


# --- complete --------------------------------------------------------------


def test_complete_removes_the_message(queue, clock):
    queue.send(_msg())
    got = queue.receive()
    queue.complete(got)
    clock.advance(LOCK * 10)
    assert queue.receive() is None
    assert queue.receive_dead_lettered() is None


def test_complete_twice_raises_lock_lost(queue):
    queue.send(_msg())
    got = queue.receive()
    queue.complete(got)
    with pytest.raises(LockLostError):
        queue.complete(got)


# --- abandon / redelivery --------------------------------------------------


def test_abandon_makes_it_visible_again_with_delivery_count_plus_one(queue):
    m = _msg()
    queue.send(m)
    first = queue.receive()
    queue.abandon(first)
    second = queue.receive()
    assert second.message == m
    assert second.delivery_count == first.delivery_count + 1
    assert second.lock_token != first.lock_token


def test_lock_expiry_makes_it_visible_again(queue, clock):
    m = _msg()
    queue.send(m)
    queue.receive()
    clock.advance(LOCK)  # locked_until == now counts as expired
    again = queue.receive()
    assert again is not None
    assert again.message == m
    assert again.delivery_count == 2


def test_redelivered_message_goes_to_the_back_of_the_queue(queue):
    a, b = _msg(), _msg()
    queue.send(a)
    queue.send(b)
    queue.abandon(queue.receive())  # a
    assert queue.receive().message == b
    assert queue.receive().message == a


# --- max delivery count → DLQ ----------------------------------------------


def test_abandoning_the_last_delivery_dead_letters_it(queue):
    m = _msg()
    queue.send(m)
    for expected_count in range(1, MAX_DELIVERIES + 1):
        got = queue.receive()
        assert got.delivery_count == expected_count
        queue.abandon(got)
    assert queue.receive() is None
    dead = queue.receive_dead_lettered()
    assert dead.message == m
    assert dead.dead_letter_reason == MAX_DELIVERY_COUNT_EXCEEDED


def test_lock_expiry_on_the_last_delivery_dead_letters_it(queue, clock):
    m = _msg()
    queue.send(m)
    for _ in range(MAX_DELIVERIES):
        assert queue.receive() is not None
        clock.advance(LOCK)
    assert queue.receive() is None
    dead = queue.receive_dead_lettered()
    assert dead.message == m
    assert dead.dead_letter_reason == MAX_DELIVERY_COUNT_EXCEEDED


# --- dead_letter -----------------------------------------------------------


def test_dead_letter_moves_it_to_the_dlq_with_the_reason(queue):
    m = _msg()
    queue.send(m)
    queue.dead_letter(queue.receive(), reason="bad payload")
    assert queue.receive() is None
    dead = queue.receive_dead_lettered()
    assert dead.message == m
    assert dead.dead_letter_reason == "bad payload"


def test_dlq_message_is_peek_locked_until_completed(queue, clock):
    queue.send(_msg())
    queue.dead_letter(queue.receive(), reason="x")
    dead = queue.receive_dead_lettered()
    assert queue.receive_dead_lettered() is None  # locked
    queue.complete(dead)
    clock.advance(LOCK * 10)
    assert queue.receive_dead_lettered() is None  # gone
    assert queue.receive() is None


def test_dlq_message_reappears_in_the_dlq_if_its_lock_expires(queue, clock):
    m = _msg()
    queue.send(m)
    queue.dead_letter(queue.receive(), reason="x")
    queue.receive_dead_lettered()
    clock.advance(LOCK)
    again = queue.receive_dead_lettered()
    assert again.message == m
    assert again.dead_letter_reason == "x"
    assert queue.receive() is None  # never back on the main queue


def test_dead_lettering_a_dlq_message_keeps_its_first_reason(queue):
    queue.send(_msg())
    queue.dead_letter(queue.receive(), reason="first")
    queue.dead_letter(queue.receive_dead_lettered(), reason="second")
    assert queue.receive_dead_lettered().dead_letter_reason == "first"
    assert queue.receive() is None


# --- renew_lock ------------------------------------------------------------


def test_renew_lock_extends_the_lock(queue, clock):
    queue.send(_msg())
    got = queue.receive()
    clock.advance(LOCK - 1)
    queue.renew_lock(got)
    assert got.locked_until == clock.now + LOCK
    clock.advance(LOCK - 1)  # past the original lock, inside the renewed one
    assert queue.receive() is None
    queue.complete(got)  # still ours


# --- LockLostError ---------------------------------------------------------


@pytest.mark.parametrize(
    "settle",
    [
        lambda q, m: q.complete(m),
        lambda q, m: q.abandon(m),
        lambda q, m: q.dead_letter(m, reason="x"),
        lambda q, m: q.renew_lock(m),
    ],
    ids=["complete", "abandon", "dead_letter", "renew_lock"],
)
def test_acting_on_an_expired_lock_raises_lock_lost(queue, clock, settle):
    queue.send(_msg())
    got = queue.receive()
    clock.advance(LOCK)
    with pytest.raises(LockLostError):
        settle(queue, got)


def test_old_delivery_cannot_settle_the_redelivery(queue, clock):
    queue.send(_msg())
    first = queue.receive()
    clock.advance(LOCK)
    second = queue.receive()  # same message, new lock token
    with pytest.raises(LockLostError):
        queue.complete(first)
    queue.complete(second)  # the current holder can
    assert queue.receive() is None
