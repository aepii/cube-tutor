from sqlmodel import SQLModel, Field, Relationship
from typing import Optional


class UserAlgorithm(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    algorithm_id: int = Field(foreign_key="algorithm.id")

    learned: bool = False
    favorited: bool = False

    user: Optional["User"] = Relationship(back_populates="algorithm")
    algorithm: Optional["Algorithm"] = Relationship(back_populates="users")
