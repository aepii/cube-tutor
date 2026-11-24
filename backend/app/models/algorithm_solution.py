from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .algorithm_case import AlgorithmCase
    from .user_algorithm import UserAlgorithm


# Defines the algorithm solution model for the database layer
class AlgorithmSolution(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "case_id", "solution", name="uq_algorithmsolution_case_solution"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="algorithmcase.id")

    solution: str
    orientation: int

    case: "AlgorithmCase" = Relationship(back_populates="solutions")
    users: list["UserAlgorithm"] = Relationship(back_populates="solution")
