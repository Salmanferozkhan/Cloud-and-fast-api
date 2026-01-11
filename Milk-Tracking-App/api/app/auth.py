"""JWT authentication utilities and dependencies."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import get_settings
from app.database import get_session
from app.models import User
from app.schemas import TokenData

settings = get_settings()

# OAuth2 password bearer scheme - token URL is relative to the auth router
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token (typically {"sub": email}).
        expires_delta: Optional custom expiration time. Defaults to settings.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode.

    Returns:
        dict | None: Decoded token payload or None if invalid.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """Dependency to get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header.
        session: Database session.

    Returns:
        User: The authenticated user.

    Raises:
        HTTPException: 401 if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    email: str | None = payload.get("sub")
    if email is None:
        raise credentials_exception

    token_data = TokenData(email=email)

    # Query user from database
    statement = select(User).where(User.email == token_data.email)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
