"""FastAPI application entry point for Milk Tracking API."""

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select

from app.database import async_session_maker, create_db_and_tables
from app.models import User
from app.routers import auth, entries, reports, suppliers, water
from app.security import hash_password


async def _seed_initial_user() -> None:
    # On single-container deploys (e.g. HF Spaces) the API port is not exposed
    # externally, so provision the agent's login user from env on first boot.
    email = os.getenv("API_EMAIL")
    password = os.getenv("API_PASSWORD")
    if not email or not password:
        return
    async with async_session_maker() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            return
        session.add(User(email=email, hashed_password=hash_password(password)))
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        None: Application is ready to handle requests.
    """
    await create_db_and_tables()
    await _seed_initial_user()
    yield


app = FastAPI(
    title="Milk Tracking API",
    description="API for tracking milk delivery and consumption",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8005",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8005",
        "http://agent:8005",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(suppliers.router, prefix="/api/v1/suppliers")
app.include_router(entries.router, prefix="/api/v1/entries")
app.include_router(reports.router, prefix="/api/v1/reports")
app.include_router(water.router, prefix="/api/v1/water")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Health status of the API.
    """
    return {"status": "healthy"}
