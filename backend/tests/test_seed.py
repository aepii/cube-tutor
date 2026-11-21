"""The seed loads the raw JSON from SEED_DATA_DIR and is safe to run twice."""

import json

from sqlmodel import func, select

from app.models import AlgorithmCase, AlgorithmSolution
from seed import seed_algorithms

RAW = {
    "f2l": {
        "subset": "F2L",
        "cases": [
            {
                "name": "F2L 1",
                "subgroup": "Free Pairs",
                "setup": "R U' R'",
                "solutions": [
                    {"alg": "U R U' R'", "orientation": "0"},
                    {"alg": "y U L U' L'", "orientation": "1"},
                ],
            }
        ],
    },
    "oll": {
        "subset": "OLL",
        "cases": [
            {
                "name": "OLL 21",
                "subgroup": "OCLL",
                "setup": "R U2 R' U' R U R' U' R U' R'",
                "solutions": [{"alg": "R U R' U R U' R' U R U2 R'", "orientation": "0"}],
            }
        ],
    },
    "pll": {
        "subset": "PLL",
        "cases": [
            {
                "name": "Ua",
                "subgroup": "Edges",
                "setup": "M2 U M U2 M' U M2",
                "solutions": [
                    {"alg": "M2 U M U2 M' U M2", "orientation": "0"},
                    {"alg": "R U' R U R U R U' R' U' R2", "orientation": "0"},
                ],
            }
        ],
    },
}


def _counts(session) -> tuple[int, int]:
    session.expire_all()
    cases = session.exec(select(func.count()).select_from(AlgorithmCase)).one()
    sols = session.exec(select(func.count()).select_from(AlgorithmSolution)).one()
    return cases, sols


def test_seed_reads_seed_data_dir_and_is_idempotent(tmp_path, monkeypatch, session):
    for name, data in RAW.items():
        (tmp_path / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("SEED_DATA_DIR", str(tmp_path))

    seed_algorithms.main()
    assert _counts(session) == (3, 5)

    seed_algorithms.main()
    assert _counts(session) == (3, 5)


def test_default_data_dir_is_repo_raw_data(monkeypatch):
    monkeypatch.delenv("SEED_DATA_DIR", raising=False)
    data_dir = seed_algorithms.data_dir()
    assert {p.name for p in data_dir.glob("*.json")} >= {"f2l.json", "oll.json", "pll.json"}
