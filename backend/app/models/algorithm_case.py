from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .algorithm_solution import AlgorithmSolution


# Defines the algorithm case model for the database layer
class AlgorithmCase(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "subset", "name", "subgroup", name="uq_algorithmcase_subset_name_subgroup"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    subset: str
    name: str
    subgroup: str
    setup: str

    solutions: list["AlgorithmSolution"] = Relationship(back_populates="case")
