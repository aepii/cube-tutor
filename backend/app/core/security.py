import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from passlib.context import CryptContext
from pydantic import SecretStr

from app.core.settings import settings

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


# Hashes a refresh token for storage and lookup.
# sha256, not bcrypt: the token is a signed JWT with a random jti, so there is
# nothing to brute-force, and a deterministic hash allows an indexed lookup.
# It also covers the whole token (bcrypt only reads the first 72 bytes).
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


# Creates a JWT access token
def create_access_token(
    subject: str, expires_delta: timedelta | None = None
) -> tuple[str, datetime]:
    # Set expiration
    if expires_delta:
        expires_at = datetime.now(UTC) + expires_delta
    else:
        expires_at = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Payload
    to_encode = {
        "sub": subject,
        "exp": expires_at,
        "type": "access",
        "jti": uuid4().hex,
    }
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
    subject: str, expires_delta: timedelta | None = None
) -> tuple[str, datetime]:
    # Set expiration
    if expires_delta:
        expires_at = datetime.now(UTC) + expires_delta
    else:
        expires_at = datetime.now(UTC) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    # Payload
    to_encode = {
        "sub": subject,
        "exp": expires_at,
        "type": "refresh",
        "jti": uuid4().hex,  # makes every token (and its hash) unique
    }
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
