"""Pytest fixtures for testing the Milk Tracking API."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.database import get_session
# Import models to register them with SQLModel.metadata
from app.models import MilkEntry, Supplier, User  # noqa: F401
from main import app

# In-memory SQLite database URL for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test async engine with aiosqlite
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# Create test async session factory
test_session_maker = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    """Override dependency for test database session.

    Yields:
        AsyncSession: Test database session.
    """
    async with test_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[None, None]:
    """Create test database tables before each test and drop after.

    Yields:
        None: Tables are created and ready for testing.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def session(test_db: None) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session.

    Args:
        test_db: Fixture that ensures tables exist.

    Yields:
        AsyncSession: Test database session.
    """
    async with test_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_db: None) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client with overridden database dependency.

    Args:
        test_db: Fixture that ensures tables exist.

    Yields:
        AsyncClient: HTTP client for testing API endpoints.
    """
    # Override the get_session dependency with test session
    app.dependency_overrides[get_session] = get_test_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Clear dependency overrides after test
    app.dependency_overrides.clear()
