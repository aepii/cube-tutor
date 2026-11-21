from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .algorithm_solution import AlgorithmSolution
    from .user import User

# Defines the user algorithm model for the database layer
class UserAlgorithm(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    algorithm_id: int = Field(foreign_key="algorithmsolution.id")

    is_learned: bool = False
    is_favorited: bool = False

    user: "User" = Relationship(back_populates="algorithms")
    solution: "AlgorithmSolution" = Relationship(back_populates="users")
