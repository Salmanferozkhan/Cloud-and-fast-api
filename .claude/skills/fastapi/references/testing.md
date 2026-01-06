# Testing FastAPI

## Setup

```bash
pip install pytest pytest-asyncio httpx
```

## Basic Testing with TestClient

```python
# test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Foo", "price": 10.5}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Foo"

def test_read_item_not_found():
    response = client.get("/items/999")
    assert response.status_code == 404
```

## Async Testing

```python
# test_async.py
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_async_root(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200
```

## Testing with Database

```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# test_users.py
def test_create_user(client):
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "secret"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

## Overriding Dependencies

```python
from main import app, get_current_user

def override_get_current_user():
    return {"username": "testuser", "role": "admin"}

app.dependency_overrides[get_current_user] = override_get_current_user

def test_protected_route(client):
    response = client.get("/admin/")
    assert response.status_code == 200
```

## Testing with Authentication

```python
@pytest.fixture
def auth_headers(client):
    # Login to get token
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_protected_endpoint(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
```

## Testing File Uploads

```python
def test_upload_file(client):
    response = client.post(
        "/upload/",
        files={"file": ("test.txt", b"file content", "text/plain")}
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"
```

## Pytest Configuration

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

## Test Structure

```
project/
├── app/
│   ├── main.py
│   └── ...
└── tests/
    ├── conftest.py      # Fixtures
    ├── test_main.py     # Basic tests
    ├── test_users.py    # User endpoint tests
    └── test_items.py    # Item endpoint tests
```

## Coverage

```bash
pip install pytest-cov

# Run with coverage
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```
