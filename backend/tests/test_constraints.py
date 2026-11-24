"""Named constraints: the schema, not the routes, rules out duplicates (4f) and
unknown job statuses (24a)."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import AlgorithmCase, AlgorithmSolution, Job, User, UserAlgorithm


@pytest.fixture
def user_id(session) -> int:
    user = User(username="alice", email="alice@example.com", hashed_password="x")
    session.add(user)
    session.commit()
    return user.id


def test_duplicate_case_is_rejected(session, algs):
    session.add(AlgorithmCase(subset="OLL", name="OLL 1", subgroup="Dot", setup="other"))
    _assert_violates(session, "uq_algorithmcase_subset_name_subgroup")


def test_duplicate_solution_is_rejected(session, algs):
    session.add(
        AlgorithmSolution(case_id=algs["oll"], solution="R U2 R2 F R F'", orientation=2)
    )
    _assert_violates(session, "uq_algorithmsolution_case_solution")


def test_duplicate_user_algorithm_is_rejected(session, algs, user_id):
    session.add(UserAlgorithm(user_id=user_id, algorithm_id=algs["oll_a"]))
    session.commit()
    session.add(UserAlgorithm(user_id=user_id, algorithm_id=algs["oll_a"], is_learned=True))
    _assert_violates(session, "uq_useralgorithm_user_algorithm")


def test_keys_are_composite(session, algs, user_id):
    # Same name in another subgroup, same notation under another case, and the
    # same user on another solution are all distinct rows.
    session.add(AlgorithmCase(subset="OLL", name="OLL 1", subgroup="Other", setup="x"))
    session.add(AlgorithmSolution(case_id=algs["pll"], solution="R U2 R2 F R F'", orientation=0))
    session.add(UserAlgorithm(user_id=user_id, algorithm_id=algs["oll_a"]))
    session.add(UserAlgorithm(user_id=user_id, algorithm_id=algs["oll_b"]))
    session.commit()


def test_bad_job_status_is_rejected(session, user_id):
    session.add(Job(type="diagnostic.echo", payload={}, status="queued", user_id=user_id))
    _assert_violates(session, "ck_job_status")


def _assert_violates(session, constraint: str) -> None:
    with pytest.raises(IntegrityError) as exc:
        session.commit()
    session.rollback()
    assert exc.value.orig.diag.constraint_name == constraint
