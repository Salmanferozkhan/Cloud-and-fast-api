# Milk Tracking Application

A chat-based milk tracking application to record daily milk purchases from multiple suppliers and generate monthly payment reports.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Chainlit (Chat UI with streaming) |
| Backend | FastAPI + SQLModel ORM |
| Database | Neon PostgreSQL (SQLite for local dev) |
| AI Agent | OpenAI Agents SDK + Gemini 2.5 Flash |
| Auth | JWT (python-jose) + pwdlib (Argon2) |

## Project Structure

```
Milk-Tracking-App/
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── config.py       # Pydantic settings
│   │   ├── database.py     # Async SQLModel setup
│   │   ├── models.py       # User, Supplier, MilkEntry
│   │   ├── schemas.py      # Request/Response schemas
│   │   ├── security.py     # Password hashing (Argon2)
│   │   ├── auth.py         # JWT authentication
│   │   └── routers/        # API endpoints
│   ├── tests/              # Pytest tests
│   ├── main.py             # FastAPI app
│   └── pyproject.toml
├── agent/                  # Chainlit + AI Agent
│   ├── agent.py            # Agent with Gemini model
│   ├── tools.py            # Function tools for API
│   ├── chainlit_app.py     # Chat UI with streaming
│   └── pyproject.toml
└── PLAN.md                 # Implementation plan
```

## Setup

### 1. API Server

```bash
cd api

# Copy environment file and configure
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# Install dependencies and run
uv sync --all-groups
uv run uvicorn main:app --reload --port 8076
```

API available at: http://localhost:8076/docs

### 2. Agent (Chainlit UI)

```bash
cd agent

# Copy environment file and configure
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and API credentials

# Install dependencies and run
uv sync
uv run chainlit run chainlit_app.py -w --port 8005
```

Chat UI available at: http://localhost:8005

## API Endpoints

### Auth
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/token` - Login, get JWT token
- `GET /api/v1/auth/me` - Get current user

### Suppliers
- `POST /api/v1/suppliers` - Create supplier
- `GET /api/v1/suppliers` - List active suppliers
- `GET /api/v1/suppliers/{id}` - Get by ID
- `PATCH /api/v1/suppliers/{id}` - Update supplier
- `DELETE /api/v1/suppliers/{id}` - Soft delete

### Entries
- `POST /api/v1/entries` - Create entry by supplier_id
- `POST /api/v1/entries/by-name` - Create by supplier name
- `GET /api/v1/entries` - List with date filters
- `PATCH /api/v1/entries/{id}` - Update entry
- `DELETE /api/v1/entries/{id}` - Delete entry

### Reports
- `GET /api/v1/reports/monthly/{year}/{month}` - Monthly report

## Chat Commands

Talk naturally with the agent:
- "Add 5 liters from Ramesh"
- "Show entries for this week"
- "Monthly report for January 2026"
- "List suppliers"
- "Add supplier Suresh, cow milk, Rs. 60/liter"

## Testing

```bash
cd api
uv run pytest -v
```

92 tests covering auth, suppliers, entries, reports, and integration.
