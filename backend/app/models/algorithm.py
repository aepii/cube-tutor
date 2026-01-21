from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class Algorithm(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    subset: str
    notation: str

    users: List["UserAlgorithm"] = Relationship(back_populates="algorithm")
