"""FastAPI application entry point for Milk Tracking API."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.routers import auth, entries, reports, suppliers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        None: Application is ready to handle requests.
    """
    # Startup: Create database tables
    await create_db_and_tables()
    yield
    # Shutdown: Cleanup if needed


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
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Health status of the API.
    """
    return {"status": "healthy"}
