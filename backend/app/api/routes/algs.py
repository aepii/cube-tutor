from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.api.schemas.algorithm import (
    AlgorithmFavoriteResponse,
    AlgorithmLearnResponse,
    CaseGroup,
    FlagUpdate,
    SolutionDetail,
)
from app.core.db import get_session
from app.core.dependencies import get_current_user
from app.models import AlgorithmCase, AlgorithmSolution, User, UserAlgorithm

router = APIRouter(prefix="/v1/algs", tags=["algs"])

Subset = Literal["F2L", "OLL", "PLL"]
Flag = Literal["is_favorited", "is_learned"]


# Endpoint for algorithm retrieval
@router.get("/", response_model=list[CaseGroup])
def read_algorithms(
    subset: Subset | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CaseGroup]:
    # Join AlgorithmCase and optionally attach the current user's AlgorithmSolution data.
    # Ordered so the list is stable between calls: subset, then case, then solution.
    statement = (
        select(AlgorithmSolution, AlgorithmCase, UserAlgorithm)
        .join(AlgorithmCase, AlgorithmSolution.case_id == AlgorithmCase.id)
        .outerjoin(
            UserAlgorithm,
            (UserAlgorithm.algorithm_id == AlgorithmSolution.id)
            & (UserAlgorithm.user_id == current_user.id),
        )
        .order_by(AlgorithmCase.subset, AlgorithmCase.id, AlgorithmSolution.id)
    )
    if subset is not None:
        statement = statement.where(AlgorithmCase.subset == subset)

    rows = session.exec(statement).all()

    # dicts keep insertion order, so the groups come out in SQL order
    grouped_cases = {}

    for solution, case, user_algo in rows:
        solution_detail = SolutionDetail(
            solution_id=solution.id,
            notation=solution.solution,
            orientation=solution.orientation,
            is_favorited=user_algo.is_favorited if user_algo else False,
            is_learned=user_algo.is_learned if user_algo else False,
        )

        if case.id not in grouped_cases:
            grouped_cases[case.id] = CaseGroup(
                case_id=case.id,
                case_name=case.name,
                subset=case.subset,
                subgroup=case.subgroup,
                setup=case.setup,
                solutions=[],
            )

        grouped_cases[case.id].solutions.append(solution_detail)

    return list(grouped_cases.values())


# Sets one of the user's flags on a solution to `value` and returns it.
# One atomic upsert on uq_useralgorithm_user_algorithm: the first call inserts the
# link row (the other flag starts False), later calls update only `flag`. Sending
# the same value twice is a no-op, and concurrent calls can't insert duplicates.
def _set_flag(
    session: Session, user_id: int, alg_id: int, flag: Flag, value: bool
) -> bool:
    if session.get(AlgorithmSolution, alg_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Algorithm not found"
        )

    statement = (
        insert(UserAlgorithm)
        .values(
            {
                "user_id": user_id,
                "algorithm_id": alg_id,
                "is_favorited": False,
                "is_learned": False,
                flag: value,  # overrides the False above for the flag being set
            }
        )
        .on_conflict_do_update(
            constraint="uq_useralgorithm_user_algorithm",
            set_={flag: value},
        )
        .returning(getattr(UserAlgorithm, flag))
    )
    stored = session.exec(statement).scalar_one()
    session.commit()
    return stored


# Endpoint for setting an algorithm's favorite flag
@router.put("/{alg_id}/favorite", response_model=AlgorithmFavoriteResponse)
def set_favorite(
    alg_id: int,
    body: FlagUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AlgorithmFavoriteResponse:
    stored = _set_flag(session, current_user.id, alg_id, "is_favorited", body.value)
    return AlgorithmFavoriteResponse(algorithm_id=alg_id, is_favorited=stored)


# Endpoint for setting an algorithm's learned flag
@router.put("/{alg_id}/learn", response_model=AlgorithmLearnResponse)
def set_learned(
    alg_id: int,
    body: FlagUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AlgorithmLearnResponse:
    stored = _set_flag(session, current_user.id, alg_id, "is_learned", body.value)
    return AlgorithmLearnResponse(algorithm_id=alg_id, is_learned=stored)
