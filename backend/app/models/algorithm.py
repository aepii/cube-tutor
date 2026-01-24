from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user_algorithm import UserAlgorithm


# Defines the algorithm model for the database layer
class Algorithm(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    subset: str
    notation: str

    users: List["UserAlgorithm"] = Relationship(back_populates="algorithm")
