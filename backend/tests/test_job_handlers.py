"""Job handlers (app/jobs/handlers.py). Pure functions: no queue, no DB."""

import pytest

from app.jobs.errors import PermanentJobError, TransientJobError
from app.jobs.handlers import HANDLERS, echo


def test_echo_returns_the_message():
    assert echo({"message": "hi"}) == {"message": "hi"}


def test_echo_fail_transient_raises_transient_error():
    with pytest.raises(TransientJobError):
        echo({"message": "hi", "fail": "transient"})


def test_echo_fail_permanent_raises_permanent_error():
    with pytest.raises(PermanentJobError):
        echo({"message": "hi", "fail": "permanent"})


def test_registry_maps_diagnostic_echo():
    assert HANDLERS["diagnostic.echo"] is echo
