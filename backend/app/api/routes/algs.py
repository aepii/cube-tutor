from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.db import get_session
from app.models import AlgorithmSolution, AlgorithmCase, User, UserAlgorithm
from app.api.schemas.algorithm import AlgorithmRead
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/v1/algs", tags=["algs"])


# Endpoint for algorithm retrieval
@router.get("/", response_model=list[AlgorithmRead])
def read_algorithms(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AlgorithmRead]:
    # Join algorithm solutions and algorithm cases on case id
    statement = select(AlgorithmSolution, AlgorithmCase).join(
        AlgorithmCase, AlgorithmSolution.case_id == AlgorithmCase.id
    )

    rows = session.exec(statement).all()

    # Flatten results
    results = []
    for solution, case in rows:
        results.append(
            {
                "solution_id": solution.id,
                "case_id": case.id,
                "case_name": case.name,
                "subset": case.subset,
                "notation": solution.solution,
                "orientation": solution.orientation,
            }
        )
    return results


# Endpoint for favoriting an algorithm
@router.post("/{alg_id}/favorite")
def favorite_algorithm(
    alg_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
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

    return {"algorithm_id": alg_id, "is_favorited": link.is_favorited}


# Endpoint for learning an algorithm
@router.post("/{alg_id}/learn")
def learn_algorithm(
    alg_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
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

    return {"algorithm_id": alg_id, "is_learned": link.is_learned}
