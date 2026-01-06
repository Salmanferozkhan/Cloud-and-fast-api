# Pytest Markers Reference

## Built-in Markers

### skip
```python
import pytest

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

# Conditional skip
@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_feature():
    pass

# Skip at runtime
def test_dynamic_skip():
    if not external_service_available():
        pytest.skip("External service unavailable")
```

### xfail (Expected Failure)
```python
@pytest.mark.xfail(reason="Known bug #123")
def test_known_bug():
    assert broken_function() == expected

# Strict xfail - fail if test passes
@pytest.mark.xfail(strict=True)
def test_must_fail():
    assert False

# Conditional xfail
@pytest.mark.xfail(
    sys.version_info < (3, 10),
    reason="Requires Python 3.10+"
)
def test_new_feature():
    pass

# Mark as xfail at runtime
def test_dynamic_xfail():
    if condition:
        pytest.xfail("Reason")
```

### parametrize
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected

# Multiple parameters
@pytest.mark.parametrize("x", [1, 2])
@pytest.mark.parametrize("y", [10, 20])
def test_multiply(x, y):
    # Runs 4 times: (1,10), (1,20), (2,10), (2,20)
    assert x * y > 0

# With IDs
@pytest.mark.parametrize("value,expected", [
    pytest.param(1, 2, id="one"),
    pytest.param(2, 4, id="two"),
    pytest.param(-1, -2, id="negative"),
])
def test_with_ids(value, expected):
    assert value * 2 == expected

# Combining with marks
@pytest.mark.parametrize("value", [
    pytest.param(1),
    pytest.param(2, marks=pytest.mark.slow),
    pytest.param(3, marks=pytest.mark.xfail),
])
def test_marked_params(value):
    assert value > 0
```

### usefixtures
```python
@pytest.mark.usefixtures("setup_database", "clear_cache")
class TestDatabase:
    def test_query(self):
        pass

    def test_insert(self):
        pass
```

## Custom Markers

### Registering Markers
```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: integration tests requiring external services",
    "unit: unit tests",
    "smoke: quick sanity checks",
]
```

### Using Custom Markers
```python
@pytest.mark.slow
def test_heavy_computation():
    pass

@pytest.mark.integration
def test_database_connection():
    pass

@pytest.mark.smoke
def test_app_starts():
    pass

# Multiple markers
@pytest.mark.slow
@pytest.mark.integration
def test_full_workflow():
    pass
```

### Running by Marker
```bash
# Run only slow tests
pytest -m slow

# Run everything except slow
pytest -m "not slow"

# Combine markers
pytest -m "slow and integration"
pytest -m "slow or integration"
pytest -m "smoke and not integration"
```

## Marker Expressions

```bash
# AND
pytest -m "slow and integration"

# OR
pytest -m "slow or smoke"

# NOT
pytest -m "not slow"

# Complex
pytest -m "(slow or integration) and not smoke"
```

## Class and Module Markers

```python
# Apply to all tests in class
@pytest.mark.integration
class TestIntegration:
    def test_one(self):
        pass

    def test_two(self):
        pass

# Apply to all tests in module
pytestmark = pytest.mark.integration

# Multiple module markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
]
```

## Marker Fixtures (conftest.py)

```python
# conftest.py
import pytest

@pytest.fixture(autouse=True)
def skip_slow_tests(request):
    """Skip tests marked slow unless --runslow is passed"""
    if request.node.get_closest_marker("slow"):
        if not request.config.getoption("--runslow"):
            pytest.skip("Need --runslow to run")

def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
```

## Dynamic Markers

```python
def pytest_collection_modifyitems(config, items):
    """Add markers dynamically based on test properties"""
    for item in items:
        # Mark all tests in integration/ folder
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark tests with "slow" in name
        if "slow" in item.name:
            item.add_marker(pytest.mark.slow)
```

## Marker Best Practices

1. **Register all markers** - Avoid warnings, enable IDE support
2. **Use descriptive names** - `integration` not `i`
3. **Document marker purpose** - In registration and usage
4. **Keep markers orthogonal** - `slow` and `integration` are separate concerns
5. **Use in CI/CD** - Run subsets: `pytest -m "not slow"` for fast feedback
