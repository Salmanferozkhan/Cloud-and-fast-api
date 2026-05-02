# ---- Base Stage: Python + uv ----
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.6 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ---- Dependencies Stage ----
FROM base AS deps

# Install native build dependencies for asyncpg, cryptography, argon2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ---- Development Stage ----
FROM base AS dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY . .

EXPOSE 8076

CMD ["uv", "run", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8076"]

# ---- Production Stage ----
FROM python:3.12-slim AS production

# Install runtime-only native libs (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy virtual environment from deps stage
COPY --from=deps /app/.venv /app/.venv

# Copy application code
COPY . .

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8076

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD curl -f http://localhost:8076/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8076", "--workers", "4"]
