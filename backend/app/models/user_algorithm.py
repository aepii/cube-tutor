from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .algorithm_solution import AlgorithmSolution
    from .user import User


# Defines the user algorithm model for the database layer
class UserAlgorithm(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "user_id", "algorithm_id", name="uq_useralgorithm_user_algorithm"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    algorithm_id: int = Field(foreign_key="algorithmsolution.id")

    is_learned: bool = False
    is_favorited: bool = False

    user: "User" = Relationship(back_populates="algorithms")
    solution: "AlgorithmSolution" = Relationship(back_populates="users")
