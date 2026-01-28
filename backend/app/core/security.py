from datetime import datetime, UTC, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from app.core.settings import settings
from pydantic import SecretStr

# Defines the hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hashes password
def hash_password(password: SecretStr) -> str:
    password = password.get_secret_value()
    return pwd_context.hash(password)


# Verifies password against hashed password
def verify_password(password: SecretStr, hashed_password: str) -> bool:
    plain_password = password.get_secret_value()
    return pwd_context.verify(plain_password, hashed_password)


# Hashes token
def hash_token(token: str) -> str:
    return pwd_context.hash(token)


# Verifies password against hashed token
def verify_token(token: str, hashed_token) -> bool:
    return pwd_context.verify(token, hashed_token)


# JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


# Creates a JWT access token
def create_access_token(
    subject: str, expires_delta: Optional[timedelta] = None
) -> tuple[str, datetime]:
    # Set expiration
    if expires_delta:
        expires_at = datetime.now(UTC) + expires_delta
    else:
        expires_at = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Payload
    to_encode = {"sub": subject, "exp": expires_at, "type": "access"}
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    # Return JWT and expiration
    return token, expires_at


# Decodes a JWT access token
def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
    return None


# Creates a JWT refresh token
def create_refresh_token(
    subject: str, expires_delta: Optional[timedelta] = None
) -> tuple[str, datetime]:
    # Set expiration
    if expires_delta:
        expires_at = datetime.now(UTC) + expires_delta
    else:
        expires_at = datetime.now(UTC) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    # Payload
    to_encode = {"sub": subject, "exp": expires_at, "type": "refresh"}
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    # Return JWT and expiration
    return token, expires_at


# Decodes a JWT refresh token
def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
    return None
