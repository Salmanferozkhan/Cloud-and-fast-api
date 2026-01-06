# Pytest Fixtures Reference

## Basic Fixtures

```python
import pytest

@pytest.fixture
def sample_data():
    return {"name": "test", "value": 42}

def test_with_fixture(sample_data):
    assert sample_data["name"] == "test"
```

## Setup and Teardown

```python
@pytest.fixture
def database():
    # Setup
    db = create_connection()
    yield db  # Test runs here
    # Teardown
    db.close()

@pytest.fixture
def temp_file():
    path = Path("temp.txt")
    path.write_text("test content")
    yield path
    path.unlink()  # Cleanup
```

## Fixture Scopes

```python
@pytest.fixture(scope="function")  # Default - per test function
def func_fixture():
    return create_resource()

@pytest.fixture(scope="class")  # Per test class
def class_fixture():
    return create_resource()

@pytest.fixture(scope="module")  # Per test file
def module_fixture():
    return create_resource()

@pytest.fixture(scope="session")  # Per test run
def session_fixture():
    return create_expensive_resource()

@pytest.fixture(scope="package")  # Per package
def package_fixture():
    return create_resource()
```

## Autouse Fixtures

```python
@pytest.fixture(autouse=True)
def reset_database(db):
    """Automatically runs before each test"""
    db.reset()
    yield
    db.cleanup()
```

## Fixture Dependencies

```python
@pytest.fixture
def config():
    return {"db_url": "sqlite:///:memory:"}

@pytest.fixture
def database(config):
    return connect(config["db_url"])

@pytest.fixture
def user(database):
    return database.create_user("test@example.com")

def test_user_created(user, database):
    assert database.get_user(user.id) is not None
```

## Fixture Factories

```python
@pytest.fixture
def make_user(database):
    created_users = []

    def _make_user(name, email=None):
        email = email or f"{name}@example.com"
        user = database.create_user(name, email)
        created_users.append(user)
        return user

    yield _make_user

    # Cleanup all created users
    for user in created_users:
        database.delete_user(user.id)

def test_multiple_users(make_user):
    user1 = make_user("alice")
    user2 = make_user("bob", "bob@custom.com")
    assert user1.name != user2.name
```

## Parametrized Fixtures

```python
@pytest.fixture(params=["mysql", "postgres", "sqlite"])
def database(request):
    db = create_database(request.param)
    yield db
    db.close()

def test_query(database):
    # Runs 3 times, once per database type
    result = database.query("SELECT 1")
    assert result == 1

# With IDs
@pytest.fixture(params=[
    pytest.param("mysql", id="mysql-db"),
    pytest.param("postgres", id="pg-db"),
])
def db(request):
    return create_database(request.param)
```

## conftest.py Fixtures

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def app():
    """Shared app instance for all tests"""
    return create_app(testing=True)

@pytest.fixture
def client(app):
    """Test client for each test"""
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """Authenticated headers"""
    response = client.post("/login", json={"user": "test", "pass": "test"})
    token = response.json["token"]
    return {"Authorization": f"Bearer {token}"}
```

## Built-in Fixtures

| Fixture | Description |
|---------|-------------|
| `tmp_path` | Temp directory as `pathlib.Path` |
| `tmp_path_factory` | Session-scoped temp path factory |
| `tmpdir` | Temp directory as `py.path.local` (legacy) |
| `capsys` | Capture stdout/stderr |
| `capfd` | Capture file descriptors |
| `caplog` | Capture logging |
| `monkeypatch` | Modify objects/environment |
| `request` | Test/fixture context |
| `pytestconfig` | Access pytest config |
| `cache` | Cross-session cache |

## Using tmp_path

```python
def test_file_operations(tmp_path):
    # tmp_path is a pathlib.Path
    file = tmp_path / "test.txt"
    file.write_text("content")
    assert file.read_text() == "content"

def test_subdirectory(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file.txt").write_text("data")
```

## Request Fixture

```python
@pytest.fixture
def resource(request):
    # Access test metadata
    print(f"Running: {request.node.name}")
    print(f"Module: {request.module.__name__}")

    # Access fixture parameters
    if hasattr(request, "param"):
        return create_resource(request.param)
    return create_resource()

@pytest.fixture
def cleanup_after(request):
    items = []
    yield items
    # Cleanup using request.addfinalizer
    def cleanup():
        for item in items:
            item.delete()
    request.addfinalizer(cleanup)
```

## Fixture Best Practices

1. **Name fixtures clearly** - `authenticated_user` not `user1`
2. **Use appropriate scope** - Don't use session scope for mutable fixtures
3. **Always cleanup** - Use `yield` for teardown
4. **Keep fixtures focused** - One responsibility per fixture
5. **Use conftest.py** - Share fixtures across test files
6. **Document complex fixtures** - Add docstrings explaining purpose
7. **Avoid fixture side effects** - Fixtures should be predictable
