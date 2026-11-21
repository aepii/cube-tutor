from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .algorithm_solution import AlgorithmSolution


# Defines the algorithm case model for the database layer
class AlgorithmCase(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    subset: str
    name: str
    subgroup: str
    setup: str

    solutions: list["AlgorithmSolution"] = Relationship(back_populates="case")
