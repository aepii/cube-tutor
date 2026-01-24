from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .algorithm import Algorithm

# Defines the user algorithm model for the database layer
class UserAlgorithm(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    algorithm_id: int = Field(foreign_key="algorithm.id")

    is_learned: bool = False
    is_favorited: bool = False

    user: Optional["User"] = Relationship(back_populates="algorithms")
    algorithm: Optional["Algorithm"] = Relationship(back_populates="users")
