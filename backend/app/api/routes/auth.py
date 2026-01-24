from fastapi import APIRouter, Depends, HTTPException, status
from app.api.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.db import get_session
from sqlmodel import Session, select
from app.models import User
from app.core.security import hash_password, create_access_token, verify_password

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

    # Create access token
    token = create_access_token(subject=str(user.id))

    return TokenResponse(access_token=token)


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

    # Create access token
    token = create_access_token(subject=str(user.id))

    return TokenResponse(access_token=token)
