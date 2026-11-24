"""Algorithms API: ordered/filterable listing with per-user flags, and the
idempotent `PUT …/favorite` / `PUT …/learn` endpoints (4f)."""

import pytest
from sqlmodel import func, select

from app.models import AlgorithmCase, AlgorithmSolution, UserAlgorithm
from tests.helpers import bearer, register

LIST = "/v1/algs/"
FLAGS = [
    ("favorite", "is_favorited", "is_learned"),
    ("learn", "is_learned", "is_favorited"),
]


def _solutions_by_id(body: list[dict]) -> dict[int, dict]:
    return {s["solution_id"]: s for case in body for s in case["solutions"]}


def _flags(client, headers, alg: int) -> tuple[bool, bool]:
    s = _solutions_by_id(client.get(LIST, headers=headers).json())[alg]
    return s["is_favorited"], s["is_learned"]


def _link_count(session) -> int:
    return session.exec(select(func.count()).select_from(UserAlgorithm)).one()


# --- GET /v1/algs/ ---------------------------------------------------------


def test_list_groups_solutions_under_their_case(client, auth_headers, algs):
    resp = client.get(LIST, headers=auth_headers)
    assert resp.status_code == 200
    cases = {c["case_id"]: c for c in resp.json()}
    assert set(cases) == {algs["oll"], algs["pll"]}

    oll = cases[algs["oll"]]
    assert (oll["case_name"], oll["subset"], oll["subgroup"], oll["setup"]) == (
        "OLL 1",
        "OLL",
        "Dot",
        "R U2 R'",
    )
    assert [s["solution_id"] for s in oll["solutions"]] == [
        algs["oll_a"],
        algs["oll_b"],
    ]
    assert [s["solution_id"] for s in cases[algs["pll"]]["solutions"]] == [
        algs["pll_a"]
    ]


def test_list_flags_start_false_for_a_new_user(client, auth_headers, algs):
    solutions = _solutions_by_id(client.get(LIST, headers=auth_headers).json())
    assert len(solutions) == 3
    for s in solutions.values():
        assert s["is_favorited"] is False
        assert s["is_learned"] is False


def test_list_is_empty_without_algorithms(client, auth_headers):
    resp = client.get(LIST, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_is_ordered_by_subset_then_case_then_solution(
    client, auth_headers, session
):
    # Cases inserted out of subset order; solutions interleaved across cases.
    pll = AlgorithmCase(subset="PLL", name="Ua", subgroup="Edges", setup="x")
    oll2 = AlgorithmCase(subset="OLL", name="OLL 2", subgroup="Dot", setup="x")
    f2l = AlgorithmCase(subset="F2L", name="F2L 1", subgroup="Basic", setup="x")
    oll1 = AlgorithmCase(subset="OLL", name="OLL 1", subgroup="Dot", setup="x")
    session.add_all([pll, oll2, f2l, oll1])
    session.commit()
    for i, case in enumerate([oll1, pll, oll2, f2l, oll1, pll, f2l, oll2]):
        session.add(AlgorithmSolution(case_id=case.id, solution=f"R{i}", orientation=0))
        session.commit()

    first = client.get(LIST, headers=auth_headers).json()
    assert [c["case_id"] for c in first] == [f2l.id, oll2.id, oll1.id, pll.id]
    for case in first:
        ids = [s["solution_id"] for s in case["solutions"]]
        assert len(ids) == 2
        assert ids == sorted(ids)
    assert client.get(LIST, headers=auth_headers).json() == first


@pytest.mark.parametrize(("subset", "key"), [("OLL", "oll"), ("PLL", "pll")])
def test_list_filters_by_subset(client, auth_headers, algs, subset, key):
    resp = client.get(LIST, params={"subset": subset}, headers=auth_headers)
    assert resp.status_code == 200
    assert [c["case_id"] for c in resp.json()] == [algs[key]]
    assert {c["subset"] for c in resp.json()} == {subset}


def test_list_filter_with_no_matches_is_empty(client, auth_headers, algs):
    resp = client.get(LIST, params={"subset": "F2L"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.parametrize("subset", ["XYZ", "oll", ""])
def test_list_rejects_unknown_subset(client, auth_headers, algs, subset):
    resp = client.get(LIST, params={"subset": subset}, headers=auth_headers)
    assert resp.status_code == 422


# --- PUT /v1/algs/{id}/favorite | /learn -----------------------------------


@pytest.mark.parametrize(("action", "flag", "other"), FLAGS)
def test_put_true_twice_is_idempotent(
    client, auth_headers, session, algs, action, flag, other
):
    alg = algs["oll_a"]
    url = f"/v1/algs/{alg}/{action}"

    for _ in range(2):
        resp = client.put(url, json={"value": True}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == {"algorithm_id": alg, flag: True}

    assert _link_count(session) == 1
    solutions = _solutions_by_id(client.get(LIST, headers=auth_headers).json())
    assert solutions[alg][flag] is True
    assert solutions[alg][other] is False
    assert solutions[algs["oll_b"]][flag] is False


@pytest.mark.parametrize(("action", "flag", "other"), FLAGS)
def test_put_false_clears_the_flag(
    client, auth_headers, session, algs, action, flag, other
):
    alg = algs["oll_a"]
    url = f"/v1/algs/{alg}/{action}"
    client.put(url, json={"value": True}, headers=auth_headers)

    for _ in range(2):
        resp = client.put(url, json={"value": False}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == {"algorithm_id": alg, flag: False}

    assert _link_count(session) == 1
    assert _flags(client, auth_headers, alg) == (False, False)


@pytest.mark.parametrize(("action", "flag", "other"), FLAGS)
def test_put_false_on_a_new_link_stores_false(
    client, auth_headers, algs, action, flag, other
):
    alg = algs["pll_a"]
    resp = client.put(
        f"/v1/algs/{alg}/{action}", json={"value": False}, headers=auth_headers
    )
    assert resp.json() == {"algorithm_id": alg, flag: False}
    assert _flags(client, auth_headers, alg) == (False, False)


def test_favorite_and_learn_are_independent(client, auth_headers, session, algs):
    alg = algs["pll_a"]
    base = f"/v1/algs/{alg}"
    client.put(f"{base}/favorite", json={"value": True}, headers=auth_headers)
    client.put(f"{base}/learn", json={"value": True}, headers=auth_headers)
    assert _flags(client, auth_headers, alg) == (True, True)

    client.put(f"{base}/favorite", json={"value": False}, headers=auth_headers)
    assert _flags(client, auth_headers, alg) == (False, True)

    client.put(f"{base}/learn", json={"value": False}, headers=auth_headers)
    client.put(f"{base}/favorite", json={"value": True}, headers=auth_headers)
    assert _flags(client, auth_headers, alg) == (True, False)
    assert _link_count(session) == 1


def test_flags_are_per_user(client, auth_headers, algs):
    alg = algs["oll_a"]
    client.put(f"/v1/algs/{alg}/favorite", json={"value": True}, headers=auth_headers)
    client.put(f"/v1/algs/{alg}/learn", json={"value": True}, headers=auth_headers)

    bob = bearer(register(client, "bob")["access_token"])
    assert _flags(client, bob, alg) == (False, False)
    client.put(f"/v1/algs/{alg}/favorite", json={"value": True}, headers=bob)
    client.put(f"/v1/algs/{alg}/favorite", json={"value": False}, headers=bob)

    assert _flags(client, auth_headers, alg) == (True, True)


@pytest.mark.parametrize("action", ["favorite", "learn"])
def test_put_on_missing_algorithm_is_404(client, auth_headers, session, action):
    resp = client.put(
        f"/v1/algs/999999/{action}", json={"value": True}, headers=auth_headers
    )
    assert resp.status_code == 404
    assert _link_count(session) == 0


@pytest.mark.parametrize("action", ["favorite", "learn"])
def test_put_requires_auth(client, algs, action):
    resp = client.put(f"/v1/algs/{algs['oll_a']}/{action}", json={"value": True})
    assert resp.status_code == 401


@pytest.mark.parametrize("action", ["favorite", "learn"])
@pytest.mark.parametrize("kwargs", [{}, {"json": {}}, {"json": {"value": None}}])
def test_put_without_value_is_422(client, auth_headers, algs, action, kwargs):
    resp = client.put(
        f"/v1/algs/{algs['oll_a']}/{action}", headers=auth_headers, **kwargs
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("action", ["favorite", "learn"])
def test_post_toggle_is_gone(client, auth_headers, algs, action):
    resp = client.post(f"/v1/algs/{algs['oll_a']}/{action}", headers=auth_headers)
    assert resp.status_code == 405
