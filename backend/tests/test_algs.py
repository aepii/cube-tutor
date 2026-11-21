"""Algorithms API: listing with per-user flags, favorite/learn toggles.

These pin today's behavior (toggle endpoints) ahead of the 4f rework to PUT.
"""

import pytest

from tests.helpers import bearer, register

LIST = "/v1/algs/"


def _solutions_by_id(body: list[dict]) -> dict[int, dict]:
    return {s["solution_id"]: s for case in body for s in case["solutions"]}


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
    assert {s["solution_id"] for s in oll["solutions"]} == {algs["oll_a"], algs["oll_b"]}
    assert [s["solution_id"] for s in cases[algs["pll"]]["solutions"]] == [algs["pll_a"]]


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


@pytest.mark.parametrize(
    ("action", "flag", "other"),
    [("favorite", "is_favorited", "is_learned"), ("learn", "is_learned", "is_favorited")],
)
def test_action_toggles_and_shows_in_list(client, auth_headers, algs, action, flag, other):
    alg = algs["oll_a"]
    url = f"/v1/algs/{alg}/{action}"

    first = client.post(url, headers=auth_headers)
    assert first.status_code == 200
    assert first.json() == {"algorithm_id": alg, flag: True}
    solutions = _solutions_by_id(client.get(LIST, headers=auth_headers).json())
    assert solutions[alg][flag] is True
    assert solutions[alg][other] is False
    assert solutions[algs["oll_b"]][flag] is False

    second = client.post(url, headers=auth_headers)
    assert second.json() == {"algorithm_id": alg, flag: False}
    solutions = _solutions_by_id(client.get(LIST, headers=auth_headers).json())
    assert solutions[alg][flag] is False


def test_favorite_and_learn_are_independent(client, auth_headers, algs):
    alg = algs["pll_a"]
    client.post(f"/v1/algs/{alg}/favorite", headers=auth_headers)
    client.post(f"/v1/algs/{alg}/learn", headers=auth_headers)
    client.post(f"/v1/algs/{alg}/favorite", headers=auth_headers)
    s = _solutions_by_id(client.get(LIST, headers=auth_headers).json())[alg]
    assert (s["is_favorited"], s["is_learned"]) == (False, True)


def test_flags_are_per_user(client, auth_headers, algs):
    alg = algs["oll_a"]
    client.post(f"/v1/algs/{alg}/favorite", headers=auth_headers)
    client.post(f"/v1/algs/{alg}/learn", headers=auth_headers)

    bob = bearer(register(client, "bob")["access_token"])
    s = _solutions_by_id(client.get(LIST, headers=bob).json())[alg]
    assert (s["is_favorited"], s["is_learned"]) == (False, False)

    s = _solutions_by_id(client.get(LIST, headers=auth_headers).json())[alg]
    assert (s["is_favorited"], s["is_learned"]) == (True, True)


@pytest.mark.parametrize("action", ["favorite", "learn"])
def test_action_on_missing_algorithm_is_404(client, auth_headers, action):
    resp = client.post(f"/v1/algs/999999/{action}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.parametrize("action", ["favorite", "learn"])
def test_action_requires_auth(client, algs, action):
    assert client.post(f"/v1/algs/{algs['oll_a']}/{action}").status_code == 401
