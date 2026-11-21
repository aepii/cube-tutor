from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, delete, select

from app.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.core.db import get_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import RefreshToken, User

router = APIRouter(prefix="/v1/auth", tags=["auth"])

# Postgres's default names for the `user` unique constraints (baseline migration)
_DUPLICATE_DETAIL = {
    "user_email_key": "Email already registered",
    "user_username_key": "Username already registered",
}


# Deletes the user's expired refresh-token rows, revoked or not.
# Runs on login and refresh, so rows can't pile up per user.
# `expires_at` is a naive UTC timestamp column, so compare with naive UTC (the
# ORM also evaluates this against rows already loaded in the session).
def _purge_expired(session: Session, user_id: int) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    session.exec(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at < now,
        )
    )


# Finds the live row for a refresh token with one indexed lookup by hash.
# Returns None if no row matches, or if it belongs to another user, is revoked
# or has expired.
def _find_live_token(
    session: Session, refresh_token: str, user_id: int
) -> RefreshToken | None:
    statement = select(RefreshToken).where(
        RefreshToken.hashed_token == hash_token(refresh_token)
    )
    db_token = session.exec(statement).first()
    if (
        db_token is None
        or db_token.user_id != user_id
        or db_token.is_revoked
        or db_token.expires_at.replace(tzinfo=UTC) <= datetime.now(UTC)
    ):
        return None
    return db_token


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

    # Update session. The pre-checks above give the friendly error in the
    # common case; the unique constraints catch a concurrent registration.
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if constraint not in _DUPLICATE_DETAIL:
            raise
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_DUPLICATE_DETAIL[constraint],
        ) from None
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

    _purge_expired(session, user.id)

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

    # Revoke the matching row, if it's still live
    db_token = _find_live_token(session, refresh_token, user_id)
    if db_token is not None:
        db_token.is_revoked = True
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

    # Look up the token's row (one indexed query by hash)
    db_token = _find_live_token(session, refresh_token, user_id)
    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found, revoked or expired",
        )

    # Clear the user's expired rows (committed with the rotation below)
    _purge_expired(session, user_id)

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
