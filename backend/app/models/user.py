from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, UTC
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr

if TYPE_CHECKING:
    from .user_algorithm import UserAlgorithm


# Defines the user model for the database layer
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=255, unique=True)
    email: EmailStr = Field(max_length=255, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    algorithms: List["UserAlgorithm"] = Relationship(back_populates="user")
