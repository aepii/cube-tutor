from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.db import get_session
from app.models import AlgorithmSolution, AlgorithmCase, User, UserAlgorithm
from app.api.schemas.algorithm import (
    SolutionDetail,
    CaseGroup,
    AlgorithmFavoriteResponse,
    AlgorithmLearnResponse,
)
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/v1/algs", tags=["algs"])


# Endpoint for algorithm retrieval
@router.get("/", response_model=list[CaseGroup])
def read_algorithms(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[CaseGroup]:
    # Join AlgorithmCase and optionally attach the current user's AlgorithmSolution data
    statement = (
        select(AlgorithmSolution, AlgorithmCase, UserAlgorithm)
        .join(AlgorithmCase, AlgorithmSolution.case_id == AlgorithmCase.id)
        .outerjoin(
            UserAlgorithm,
            (UserAlgorithm.algorithm_id == AlgorithmSolution.id)
            & (UserAlgorithm.user_id == current_user.id),
        )
    )

    rows = session.exec(statement).all()

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


# Endpoint for favoriting an algorithm
@router.post("/{alg_id}/favorite", response_model=AlgorithmFavoriteResponse)
def favorite_algorithm(
    alg_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AlgorithmFavoriteResponse:
    # Ensure algorithm exists
    alg = session.get(AlgorithmSolution, alg_id)
    if not alg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Algorithm not found"
        )

    statement = select(UserAlgorithm).where(
        UserAlgorithm.user_id == current_user.id, UserAlgorithm.algorithm_id == alg_id
    )

    link = session.exec(statement).first()

    # Create/update user algorithm entry
    if not link:
        link = UserAlgorithm(
            user_id=current_user.id,
            algorithm_id=alg_id,
            is_favorited=True,
            is_learned=False,
        )
        session.add(link)
    else:
        link.is_favorited = not link.is_favorited

    session.commit()
    session.refresh(link)

    return AlgorithmFavoriteResponse(
        algorithm_id=alg_id,
        is_favorited=link.is_favorited,
    )


# Endpoint for learning an algorithm
@router.post("/{alg_id}/learn", response_model=AlgorithmLearnResponse)
def learn_algorithm(
    alg_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AlgorithmLearnResponse:
    # Ensure algorithm exists
    alg = session.get(AlgorithmSolution, alg_id)
    if not alg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Algorithm not found"
        )

    statement = select(UserAlgorithm).where(
        UserAlgorithm.user_id == current_user.id, UserAlgorithm.algorithm_id == alg_id
    )

    link = session.exec(statement).first()

    # Create/update user algorithm entry
    if not link:
        link = UserAlgorithm(
            user_id=current_user.id,
            algorithm_id=alg_id,
            is_favorited=False,
            is_learned=True,
        )
        session.add(link)
    else:
        link.is_learned = not link.is_learned

    session.commit()
    session.refresh(link)

    return AlgorithmLearnResponse(
        algorithm_id=alg_id,
        is_learned=link.is_learned,
    )
