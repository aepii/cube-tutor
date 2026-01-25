from pathlib import Path
import json
from sqlmodel import select
from app.core.db import db_context
from app.models.algorithm_solution import AlgorithmSolution
from app.models.algorithm_case import AlgorithmCase

DATA_DIR = Path("/app/data/raw")

# Read raw data
with open(DATA_DIR / "f2l.json", encoding="utf-8") as f:
    f2l_data = json.load(f)

with open(DATA_DIR / "oll.json", encoding="utf-8") as f:
    oll_data = json.load(f)

with open(DATA_DIR / "pll.json", encoding="utf-8") as f:
    pll_data = json.load(f)

# Seed the database
with db_context() as session:
    for data in [f2l_data, oll_data, pll_data]:

        subset = data["subset"]
        cases = data["cases"]

        for case_data in cases:
            name = case_data["name"]
            subgroup = case_data["subgroup"]
            setup = case_data["setup"]
            solutions = case_data["solutions"]

            # Check if algorithm case already exists
            statement = select(AlgorithmCase).where(
                AlgorithmCase.subset == subset,
                AlgorithmCase.name == name,
                AlgorithmCase.subgroup == subgroup,
            )
            existing_case = session.exec(statement).first()

            # Insert case into datacase
            if existing_case:
                case = existing_case
            else:
                case = AlgorithmCase(
                    subset=subset, name=name, subgroup=subgroup, setup=setup
                )
                session.add(case)
                session.commit()
                session.refresh(case)

            for solution_data in solutions:
                alg_solution = solution_data["alg"]
                orientation = solution_data["orientation"]

                # Check if algorithm solution already exists
                statement = select(AlgorithmSolution).where(
                    AlgorithmSolution.case_id == case.id,
                    AlgorithmSolution.solution == alg_solution,
                    AlgorithmSolution.orientation == orientation,
                )
                existing_solution = session.exec(statement).first()

                # Insert solution into datacase
                if not existing_solution:
                    solution = AlgorithmSolution(
                        case_id=case.id, orientation=orientation, solution=alg_solution
                    )
                    session.add(solution)

    session.commit()
