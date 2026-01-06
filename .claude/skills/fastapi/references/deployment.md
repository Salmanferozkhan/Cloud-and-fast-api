# Deployment

## Docker

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY ./app ./app

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Multi-stage Build

```dockerfile
# Build stage
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# Production stage
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*
COPY ./app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Production Server (Gunicorn + Uvicorn)

```bash
pip install gunicorn uvicorn[standard]

# Run
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

```dockerfile
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

## Environment Variables

```python
# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "My API"
    debug: bool = False
    database_url: str
    secret_key: str

    model_config = {"env_file": ".env"}

@lru_cache
def get_settings():
    return Settings()
```

```env
# .env
DATABASE_URL=postgresql://user:password@localhost/dbdb
SECRET_KEY=your-super-secret-key
DEBUG=false
```

## Nginx Reverse Proxy

```nginx
# nginx.conf
upstream api {
    server api:8000;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Health Checks

```python
from fastapi import FastAPI, status

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check(db = Depends(get_db)):
    try:
        # Check DB connection
        db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(503, "Database not ready")
```

## Logging

```python
import logging
from fastapi import Request
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"completed in {process_time:.4f}s "
        f"status={response.status_code}"
    )
    return response
```

## Cloud Deployment

### Railway / Render / Fly.io

```toml
# fly.toml
app = "my-fastapi-app"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8000
  force_https = true

[env]
  PORT = "8000"
```

### Procfile (Heroku/Railway)

```procfile
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```
