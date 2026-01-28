from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator


# Defines the schema for a register request
class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=255)
    password: SecretStr = Field(...)

    @field_validator("password")
    @classmethod
    def password_length(cls, v: SecretStr) -> SecretStr:
        if not (8 <= len(v.get_secret_value()) <= 255):
            raise ValueError("Password must be 8-255 characters")
        return v


# Defines the schema for a login request
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    password: SecretStr = Field(...)

    @field_validator("password")
    @classmethod
    def password_length(cls, v: SecretStr) -> SecretStr:
        if not (8 <= len(v.get_secret_value()) <= 255):
            raise ValueError("Password must be 8-255 characters")
        return v


# Defines the schema for a logout request
class LogoutRequest(BaseModel):
    refresh_token: str


# Defines the schema for a refresh request
class RefreshRequest(BaseModel):
    refresh_token: str


# Defines the schema for a token response
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
