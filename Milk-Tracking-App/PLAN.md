# Milk Tracking Application - Implementation Plan

## Overview

A chat-based milk tracking application to record daily milk purchases from multiple suppliers and generate monthly payment reports.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Chainlit (Chat UI with streaming) |
| Backend | FastAPI + Dependency Injection |
| Database | Neon (PostgreSQL) + SQLModel ORM |
| AI Agent | OpenAI Agents SDK + Gemini 2.5 Flash |
| Auth | JWT (python-jose) + pwdlib (Argon2) |
| Testing | Pytest (TDD approach) |

---

## Project Structure

```
Milk-Tracking-App/
├── api/                           # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py              # Pydantic settings
│   │   ├── database.py            # Async engine + session
│   │   ├── models.py              # SQLModel models
│   │   ├── schemas.py             # Request/Response schemas
│   │   ├── security.py            # Password hashing (pwdlib + Argon2)
│   │   ├── auth.py                # JWT token + get_current_user
│   │   └── api.py                 # API endpoints
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py            # Test fixtures
│   │   ├── test_auth.py           # Auth tests
│   │   ├── test_suppliers.py
│   │   ├── test_entries.py
│   │   └── test_reports.py
│   ├── main.py                    # FastAPI app
│   ├── pyproject.toml
│   └── .env.example
├── agent/                         # Chainlit + OpenAI Agents
│   ├── agent.py                   # Agent definition
│   ├── tools.py                   # Function tools
│   ├── chainlit_app.py            # Chat UI
│   ├── pyproject.toml
│   └── .env.example
├── PLAN.md
└── README.md
```

---

## Database Schema

### User Table

```python
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(SQLModel):
    email: str
    password: str
```

### Supplier Table

```python
class MilkType(str, Enum):
    COW = "cow"
    BUFFALO = "buffalo"

class Supplier(SQLModel, table=True):
    __tablename__ = "suppliers"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(..., min_length=1, max_length=100, unique=True)
    milk_type: MilkType
    rate_per_liter: float = Field(..., gt=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    entries: list["MilkEntry"] = Relationship(back_populates="supplier")
```

### MilkEntry Table

```python
class MilkEntry(SQLModel, table=True):
    __tablename__ = "milk_entries"

    id: int | None = Field(default=None, primary_key=True)
    date: date
    supplier_id: int = Field(..., foreign_key="suppliers.id")
    liters: float = Field(..., gt=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    supplier: Supplier = Relationship(back_populates="entries")
```

---

## API Endpoints

### Auth (`/api/v1/auth`) - Public

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register new user |
| POST | `/login` | Login, returns JWT access token |
| GET | `/me` | Get current user (protected) |

### Suppliers (`/api/v1/suppliers`) - Protected

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create supplier |
| GET | `/` | List active suppliers |
| GET | `/{id}` | Get supplier by ID |
| GET | `/by-name/{name}` | Get supplier by name |
| PATCH | `/{id}` | Update supplier |
| DELETE | `/{id}` | Soft-delete supplier |

### Entries (`/api/v1/entries`) - Protected

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create entry by supplier_id |
| POST | `/by-name` | Create entry by supplier name |
| GET | `/` | List entries (with date filters) |
| GET | `/{id}` | Get entry by ID |
| PATCH | `/{id}` | Update entry |
| DELETE | `/{id}` | Delete entry |

### Reports (`/api/v1/reports`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/monthly/{year}/{month}` | Monthly payment report |

---

## Auth Implementation (Reference Code)

### security.py - Password Hashing (pwdlib + Argon2)

```python
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

password_hash = PasswordHash((Argon2Hasher(),))

def hash_password(password: str) -> str:
    """Hash a password with Argon2."""
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return password_hash.verify(plain_password, hashed_password)
```

### auth.py - JWT Token Functions

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from config import get_settings

settings = get_settings()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
```

### get_current_user Dependency

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise credentials_exception
    return user
```

### Login Endpoint (/token)

```python
@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where(User.email == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

---

## Agent Function Tools

```python
@function_tool
async def add_milk_entry(supplier_name: str, liters: float, entry_date: str | None = None) -> str:
    """Add a milk entry for a supplier."""

@function_tool
async def list_entries(start_date: str | None = None, end_date: str | None = None) -> str:
    """List milk entries with optional date filtering."""

@function_tool
async def get_monthly_report(year: int, month: int) -> str:
    """Get monthly report with totals per supplier."""

@function_tool
async def list_suppliers() -> str:
    """List all active suppliers with rates."""

@function_tool
async def update_supplier_rate(supplier_id: int, new_rate: float) -> str:
    """Update supplier's rate per liter."""

@function_tool
async def add_supplier(name: str, milk_type: str, rate: float) -> str:
    """Add a new milk supplier."""
```

---

## Implementation Phases (TDD)

> **Agent Usage**: Use `backend-architect` subagent for Phases 1-6 (API development). Use `frontend-developer` subagent for Phase 7 (Chainlit UI).

### Phase 1: API Project Setup *(backend-architect)*
- [ ] Create `api/` directory structure
- [ ] Create `pyproject.toml` with dependencies (including JWT libs)
- [ ] Create `app/config.py` with Settings (JWT_SECRET, JWT_ALGORITHM)
- [ ] Create `app/database.py` with async engine
- [ ] Create `tests/conftest.py` with fixtures

### Phase 2: Auth Module (JWT) *(backend-architect)*
- [ ] Write `test_auth.py` tests first
- [ ] Create User model in `app/models.py`
- [ ] Create Auth schemas (UserCreate, Token)
- [ ] Create `app/security.py` with:
  - `hash_password()` using pwdlib + Argon2
  - `verify_password()` for login
- [ ] Create `app/auth.py` with:
  - `create_access_token()` using python-jose
  - `decode_token()` for verification
  - `get_current_user` dependency with OAuth2PasswordBearer
- [ ] Implement `/users/signup`, `/token`, `/users/me` endpoints
- [ ] Run tests, ensure passing

### Phase 3: Supplier Module *(backend-architect)*
- [ ] Write `test_suppliers.py` tests first
- [ ] Create `app/models.py` with Supplier model
- [ ] Create `app/schemas.py` with Supplier schemas
- [ ] Implement Supplier CRUD in `app/api.py`
- [ ] Run tests, ensure passing

### Phase 4: MilkEntry Module *(backend-architect)*
- [ ] Write `test_entries.py` tests first
- [ ] Add MilkEntry model to `app/models.py`
- [ ] Add MilkEntry schemas to `app/schemas.py`
- [ ] Implement Entry CRUD in `app/api.py`
- [ ] Implement `/by-name` endpoint
- [ ] Run tests, ensure passing

### Phase 5: Reports Module *(backend-architect)*
- [ ] Write `test_reports.py` tests first
- [ ] Add Report schemas to `app/schemas.py`
- [ ] Implement monthly report aggregation
- [ ] Run tests, ensure passing

### Phase 6: Main App Integration *(backend-architect)*
- [ ] Create `main.py` with lifespan
- [ ] Add all routers
- [ ] Add health endpoint
- [ ] Full API integration test

### Phase 7: Agent Setup *(frontend-developer)*
- [ ] Create `agent/` directory structure
- [ ] Create `pyproject.toml`
- [ ] Create `tools.py` with all function tools
- [ ] Create `agent.py` with Gemini model
- [ ] Create `chainlit_app.py` with streaming

### Phase 8: End-to-End Testing
- [ ] Seed test suppliers
- [ ] Test conversation flows
- [ ] Verify streaming works
- [ ] Test monthly report generation

---

## Sample Conversations

### Adding Entry
```
User: Today I got 2.5 liters from milk shop
Agent: Recorded: 2.5L of buffalo milk from Milk Shop on 2024-01-10
```

### Monthly Report
```
User: Give me January 2024 report

Agent:
Monthly Report: 1/2024
------------------------------------------------------------
Supplier             Type       Liters     Rate     Amount
------------------------------------------------------------
Milk Shop            buffalo     75.00    80.00    6000.00
Delivery Person      cow         45.00    60.00    2700.00
------------------------------------------------------------
TOTAL                           120.00             8700.00
```

---

## Dependencies

> **Package Manager**: Use `uv` for all dependency management (not pip).

### API (`api/pyproject.toml`)

```toml
[project]
name = "milk-tracking-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "pydantic-settings>=2.0.0",
    "sqlmodel>=0.0.22",
    "asyncpg>=0.30.0",
    "python-dotenv>=1.0.0",
    "python-jose[cryptography]>=3.3.0",
    "pwdlib[argon2]>=0.2.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "aiosqlite>=0.20.0",
    "pytest-cov>=5.0.0",
]
```

**Setup commands:**
```bash
cd api
uv sync --all-groups    # Install all dependencies
uv run pytest           # Run tests
uv run fastapi dev      # Start dev server
```

### Agent (`agent/pyproject.toml`)

```toml
[project]
name = "milk-tracking-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "openai-agents>=0.1.0",
    "openai>=1.0.0",
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    "chainlit>=2.0.0",
]
```

**Setup commands:**
```bash
cd agent
uv sync                 # Install dependencies
uv run chainlit run chainlit_app.py  # Start Chainlit
```

---

## Reference Files (Existing Patterns)

| Pattern | Source File |
|---------|-------------|
| SQLModel models | `todoApp/app/models.py` |
| FastAPI router + DI | `todoApp/app/api.py` |
| Test fixtures | `todoApp/tests/conftest.py` |
| Agent + Gemini | `todoAgent/agent.py` |
| Function tools | `todoAgent/tools.py` |
| Chainlit streaming | `todoAgent/chainlit_app.py` |

---

## Verification Checklist

- [ ] All pytest tests passing
- [ ] API responds on `http://localhost:8080`
- [ ] JWT auth works (register, login, get token)
- [ ] Protected endpoints require valid token
- [ ] Chainlit UI runs on `http://localhost:8005`
- [ ] Can add milk entries via chat
- [ ] Can generate monthly reports via chat
- [ ] Streaming works in Chainlit
- [ ] Database persists in Neon
