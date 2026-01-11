"""Authentication router for user registration and login."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth import CurrentUser, create_access_token
from app.database import get_session
from app.models import User
from app.schemas import Token, UserCreate, UserResponse
from app.security import hash_password, verify_password

router = APIRouter(tags=["auth"])

# Type alias for database session dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password.",
)
async def register(user_data: UserCreate, session: SessionDep) -> User:
    """Register a new user.

    Args:
        user_data: User registration data (email, password).
        session: Database session.

    Returns:
        User: The created user (password excluded in response).

    Raises:
        HTTPException: 400 if email is already registered.
    """
    # Check if email already exists
    statement = select(User).where(User.email == user_data.email)
    result = await session.execute(statement)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user with hashed password
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.post(
    "/token",
    response_model=Token,
    summary="Login for access token",
    description="OAuth2 compatible token login, get an access token for future requests.",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    """Authenticate user and return JWT access token.

    Args:
        form_data: OAuth2 password request form (username=email, password).
        session: Database session.

    Returns:
        Token: JWT access token.

    Raises:
        HTTPException: 401 if credentials are incorrect.
    """
    # Find user by email (username field contains email)
    statement = select(User).where(User.email == form_data.username)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's information.",
)
async def get_me(current_user: CurrentUser) -> User:
    """Get the current authenticated user.

    Args:
        current_user: The authenticated user from JWT token.

    Returns:
        User: The current user (password excluded in response).
    """
    return current_user
