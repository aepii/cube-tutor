from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .algorithm_case import AlgorithmCase
    from .user_algorithm import UserAlgorithm


# Defines the algorithm solution model for the database layer
class AlgorithmSolution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="algorithmcase.id")

    solution: str
    orientation: int

    case: "AlgorithmCase" = Relationship(back_populates="solutions")
    users: List["UserAlgorithm"] = Relationship(back_populates="solution")
