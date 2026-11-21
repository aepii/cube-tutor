"""Load the scraped algorithms (shared/data/raw/*.json) into Postgres.

Idempotent: rows that already exist are skipped, so it runs on every container
start (the Compose `migrate` service) and by hand:

    python -m seed.seed_algorithms
"""

import json
import os
from pathlib import Path

from sqlmodel import select

from app.core.db import db_context
from app.models.algorithm_case import AlgorithmCase
from app.models.algorithm_solution import AlgorithmSolution

SUBSETS = ("f2l", "oll", "pll")

# backend/seed/ → repo root in a checkout; /app/seed/ → / in the image, where the
# Dockerfile copies the data to /shared/data/raw. Same relative path either way.
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "shared" / "data" / "raw"


def data_dir() -> Path:
    """`SEED_DATA_DIR` if set, else the raw data next to the code."""
    override = os.environ.get("SEED_DATA_DIR")
    return Path(override) if override else DEFAULT_DATA_DIR


def load_raw(directory: Path) -> list[dict]:
    datasets = []
    for name in SUBSETS:
        with open(directory / f"{name}.json", encoding="utf-8") as f:
            datasets.append(json.load(f))
    return datasets


def seed(datasets: list[dict]) -> None:
    with db_context() as session:
        for data in datasets:
            subset = data["subset"]

            for case_data in data["cases"]:
                name = case_data["name"]
                subgroup = case_data["subgroup"]

                case = session.exec(
                    select(AlgorithmCase).where(
                        AlgorithmCase.subset == subset,
                        AlgorithmCase.name == name,
                        AlgorithmCase.subgroup == subgroup,
                    )
                ).first()

                if case is None:
                    case = AlgorithmCase(
                        subset=subset,
                        name=name,
                        subgroup=subgroup,
                        setup=case_data["setup"],
                    )
                    session.add(case)
                    session.commit()  # need case.id for the solutions
                    session.refresh(case)

                for solution_data in case_data["solutions"]:
                    alg = solution_data["alg"]
                    orientation = solution_data["orientation"]

                    existing = session.exec(
                        select(AlgorithmSolution).where(
                            AlgorithmSolution.case_id == case.id,
                            AlgorithmSolution.solution == alg,
                            AlgorithmSolution.orientation == orientation,
                        )
                    ).first()

                    if existing is None:
                        session.add(
                            AlgorithmSolution(
                                case_id=case.id, orientation=orientation, solution=alg
                            )
                        )

        session.commit()


def main() -> None:
    directory = data_dir()
    seed(load_raw(directory))
    print(f"Seeded algorithms from {directory}", flush=True)


if __name__ == "__main__":
    main()
