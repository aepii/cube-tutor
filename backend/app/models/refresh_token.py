from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .user import User


# Defines the refresh token model for the database layer
class RefreshToken(SQLModel, table=True):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )
    user_id: int = Field(foreign_key="user.id")
    hashed_token: str = Field(index=True, unique=True)
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: "User" = Relationship(back_populates="refresh_tokens")
