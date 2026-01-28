from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from app.core.db import get_session
from sqlmodel import Session, select
from app.models import User, RefreshToken
from app.core.security import (
    hash_password,
    hash_token,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
    verify_token,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


# Endpoint for user registration
@router.post("/register", response_model=TokenResponse)
def register(
    data: RegisterRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    # Check if email already exists
    email_exists = select(User).where(User.email == data.email)
    email_dupe = session.exec(email_exists).first()

    if email_dupe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    username_exists = select(User).where(User.username == data.username)
    username_dupe = session.exec(username_exists).first()

    if username_dupe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create user
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )

    # Update session
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create tokens
    access_token, _ = create_access_token(subject=str(user.id))
    refresh_token, expires_at = create_refresh_token(subject=str(user.id))

    # Store refresh token
    rt = RefreshToken(
        user_id=user.id,
        hashed_token=hash_token(refresh_token),
        expires_at=expires_at,
    )

    session.add(rt)
    session.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# Endpoint for user login
@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    # Check if username is valid
    username_valid = select(User).where(User.username == data.username)
    user = session.exec(username_valid).first()

    # Check if user exists and password is correct
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Create tokens
    access_token, _ = create_access_token(subject=str(user.id))
    refresh_token, expires_at = create_refresh_token(subject=str(user.id))

    # Store refresh token
    rt = RefreshToken(
        user_id=user.id,
        hashed_token=hash_token(refresh_token),
        expires_at=expires_at,
    )

    session.add(rt)
    session.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# Endpoint for user logout
@router.post("/logout")
def logout(
    data: LogoutRequest,
    session: Session = Depends(get_session),
):
    # Get refresh token
    refresh_token = data.refresh_token

    # Get payload
    payload = decode_refresh_token(refresh_token)
    if payload is None:
        return {"detail": "Already logged out"}
    user_id = int(payload["sub"])

    # Get all user's refresh tokens
    statement = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False,
    )
    tokens = session.exec(statement).all()

    for token in tokens:
        if verify_token(refresh_token, token.hashed_token):
            token.is_revoked = True
            break

    session.commit()
    return {"detail": "Logged out"}


# Endpoint for refreshing tokens
@router.post("/refresh", response_model=TokenResponse)
def refresh(
    data: RefreshRequest,
    session: Session = Depends(get_session),
) -> TokenResponse:
    # Get refresh token
    refresh_token = data.refresh_token

    # Get payload
    payload = decode_refresh_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
    user_id = int(payload["sub"])

    # Get all user's refresh tokens
    statement = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False,
    )
    tokens = session.exec(statement).all()

    # Match hashed token with user's refresh tokens
    db_token = None
    for token in tokens:
        if verify_token(refresh_token, token.hashed_token):
            db_token = token
            break

    # No refresh token found
    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or revoked",
        )

    # Refresh token expired
    if db_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        session.delete(db_token)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Revoke the token
    db_token.is_revoked = True

    # Create new tokens
    new_access_token, _ = create_access_token(subject=str(user_id))
    new_refresh_token, expires_at = create_refresh_token(subject=str(user_id))

    # Store new refresh token
    new_rt = RefreshToken(
        user_id=user_id,
        hashed_token=hash_token(new_refresh_token),
        expires_at=expires_at,
    )

    session.add(new_rt)
    session.commit()

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)
