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


# Verifies plain password against hashed password
def verify_password(plain_password: SecretStr, hashed_password: str) -> bool:
    plain_password = plain_password.get_secret_value()
    return pwd_context.verify(plain_password, hashed_password)


# JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day


# Creates a JWT access token
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    # Set expiration
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Payload
    to_encode = {"sub": subject, "exp": expire}

    # JWT
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


# Decodes a JWT access token
def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
    return None
