from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, UTC
from pydantic import EmailStr


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=255, unique=True)
    email: EmailStr = Field(max_length=255, unique=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.now(UTC))

    algorithms: List["UserAlgorithm"] = Relationship(back_populates="user")
