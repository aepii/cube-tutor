from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .algorithm_solution import AlgorithmSolution


# Defines the algorithm case model for the database layer
class AlgorithmCase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    subset: str
    name: str
    subgroup: str
    setup: str

    solutions: List["AlgorithmSolution"] = Relationship(back_populates="case")
