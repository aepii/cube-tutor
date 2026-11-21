from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .refresh_token import RefreshToken
    from .user_algorithm import UserAlgorithm


# Defines the user model for the database layer
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=255, unique=True)
    email: EmailStr = Field(max_length=255, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    algorithms: list["UserAlgorithm"] = Relationship(back_populates="user")
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")