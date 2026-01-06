# Pytest Plugins Reference

## Essential Plugins

### pytest-cov (Coverage)
```bash
pip install pytest-cov
```

```bash
# Basic coverage
pytest --cov=mypackage

# With report
pytest --cov=mypackage --cov-report=html
pytest --cov=mypackage --cov-report=term-missing

# Multiple packages
pytest --cov=src --cov=lib

# Fail under threshold
pytest --cov=mypackage --cov-fail-under=80
```

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

### pytest-xdist (Parallel)
```bash
pip install pytest-xdist
```

```bash
# Auto-detect CPUs
pytest -n auto

# Specific workers
pytest -n 4

# Distribute by file
pytest -n 4 --dist loadfile

# Distribute by group
pytest -n 4 --dist loadgroup
```

### pytest-asyncio (Async Testing)
```bash
pip install pytest-asyncio
```

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result == expected

# Async fixtures
@pytest.fixture
async def async_client():
    client = await create_client()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_with_async_fixture(async_client):
    result = await async_client.get("/")
    assert result.status == 200
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # No need for @pytest.mark.asyncio
```

### pytest-mock
```bash
pip install pytest-mock
```

```python
def test_with_mocker(mocker):
    mock = mocker.patch("module.function")
    mock.return_value = "mocked"
    # See mocking.md for full reference
```

### pytest-timeout
```bash
pip install pytest-timeout
```

```python
@pytest.mark.timeout(10)  # 10 seconds
def test_slow_operation():
    pass

# Global timeout
# pytest --timeout=30
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
timeout = 30
```

## Web Framework Plugins

### pytest-django
```bash
pip install pytest-django
```

```python
# conftest.py
import pytest

@pytest.fixture(scope="session")
def django_db_setup():
    pass  # Custom DB setup if needed

# pytest.ini or pyproject.toml
# DJANGO_SETTINGS_MODULE = myproject.settings
```

```python
import pytest

@pytest.mark.django_db
def test_user_creation():
    from django.contrib.auth.models import User
    user = User.objects.create_user("test", "test@example.com")
    assert User.objects.count() == 1

@pytest.mark.django_db(transaction=True)
def test_with_transaction():
    pass

# Use Django test client
def test_view(client):
    response = client.get("/")
    assert response.status_code == 200

# Authenticated client
def test_auth_view(admin_client):
    response = admin_client.get("/admin/")
    assert response.status_code == 200
```

### pytest-flask
```bash
pip install pytest-flask
```

```python
# conftest.py
import pytest
from myapp import create_app

@pytest.fixture
def app():
    app = create_app(testing=True)
    yield app

@pytest.fixture
def client(app):
    return app.test_client()
```

```python
def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello" in response.data
```

### pytest-httpx (FastAPI/HTTPX)
```bash
pip install pytest-httpx
```

```python
import pytest
from httpx import AsyncClient
from myapp import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_endpoint(client):
    response = await client.get("/items")
    assert response.status_code == 200
```

## Database Plugins

### pytest-postgresql
```bash
pip install pytest-postgresql
```

```python
def test_with_postgres(postgresql):
    cursor = postgresql.cursor()
    cursor.execute("CREATE TABLE test (id serial PRIMARY KEY)")
    postgresql.commit()
```

### pytest-mongodb
```bash
pip install pytest-mongodb
```

```python
def test_with_mongo(mongodb):
    collection = mongodb["test_collection"]
    collection.insert_one({"name": "test"})
    assert collection.count_documents({}) == 1
```

## Utility Plugins

### pytest-env
```bash
pip install pytest-env
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
env = [
    "DATABASE_URL=sqlite:///:memory:",
    "DEBUG=true",
]
```

### pytest-randomly
```bash
pip install pytest-randomly
```

```bash
# Run with random order
pytest -p randomly

# Reproduce with seed
pytest -p randomly --randomly-seed=12345
```

### pytest-repeat
```bash
pip install pytest-repeat
```

```bash
# Run each test multiple times
pytest --count=10

# Or mark specific test
@pytest.mark.repeat(5)
def test_flaky():
    pass
```

### pytest-freezegun
```bash
pip install pytest-freezegun
```

```python
@pytest.mark.freeze_time("2024-01-15")
def test_with_frozen_time():
    from datetime import datetime
    assert datetime.now().year == 2024
```

### pytest-lazy-fixture
```bash
pip install pytest-lazy-fixture
```

```python
from pytest_lazyfixture import lazy_fixture

@pytest.mark.parametrize("user", [
    lazy_fixture("admin_user"),
    lazy_fixture("regular_user"),
])
def test_permissions(user):
    pass
```

## Plugin Configuration

```toml
# pyproject.toml - Common plugin settings
[tool.pytest.ini_options]
# pytest-cov
addopts = "--cov=src --cov-report=term-missing"

# pytest-asyncio
asyncio_mode = "auto"

# pytest-timeout
timeout = 30

# pytest-env
env = [
    "ENV=test",
]

# Disable plugins
addopts = "-p no:randomly"
```

## Writing Custom Plugins

```python
# conftest.py or separate plugin file
import pytest

def pytest_configure(config):
    """Called after command line args parsed"""
    config.addinivalue_line("markers", "custom: custom marker")

def pytest_collection_modifyitems(config, items):
    """Modify collected tests"""
    for item in items:
        if "slow" in item.nodeid:
            item.add_marker(pytest.mark.slow)

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Custom test reporting"""
    pass

# Register as plugin
# pytest_plugins = ["mypackage.pytest_plugin"]
```
