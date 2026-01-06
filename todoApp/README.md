# Todo API

FastAPI Todo App with SQLModel and async PostgreSQL (Neon).

## Setup

1. Install dependencies using uv:
```bash
uv sync
```

Or with pip:
```bash
pip install -e ".[dev]"
```

2. Create `.env` file from template:
```bash
cp .env.example .env
# Edit .env with your Neon PostgreSQL connection string
```

## Running the Server

Start the server with uvicorn:

```bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

Or without uv:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

Or using FastAPI CLI:
```bash
fastapi dev main.py --port 8080
```

## API Access

- **Swagger UI**: http://127.0.0.1:8080/docs
- **ReDoc**: http://127.0.0.1:8080/redoc
- **Health Check**: http://127.0.0.1:8080/health

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/v1/todos | Create todo |
| GET | /api/v1/todos | List todos |
| GET | /api/v1/todos/{id} | Get todo |
| PATCH | /api/v1/todos/{id} | Update todo |
| DELETE | /api/v1/todos/{id} | Delete todo |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test
pytest tests/test_todos.py::TestCreateTodo -v
```

## Project Structure

```
todoapp/
├── main.py              # FastAPI app entry point
├── app/
│   ├── config.py        # Settings (pydantic-settings)
│   ├── database.py      # Async engine and session
│   ├── models.py        # SQLModel table (Todo)
│   ├── schemas.py       # API schemas (Create, Update, Public)
│   └── api.py           # Router with CRUD endpoints
└── tests/
    ├── conftest.py      # Pytest fixtures
    └── test_todos.py    # All tests
```
