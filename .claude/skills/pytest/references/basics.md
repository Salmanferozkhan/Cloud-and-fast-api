# Pytest Basics Reference

## Test Discovery

Pytest automatically discovers tests following these conventions:
- Files: `test_*.py` or `*_test.py`
- Functions: `test_*`
- Classes: `Test*` (no `__init__` method)
- Methods in classes: `test_*`

## Running Tests

```bash
# Run all tests
pytest

# Run specific file
pytest test_module.py

# Run specific test
pytest test_module.py::test_function
pytest test_module.py::TestClass::test_method

# Run by keyword match
pytest -k "login or signup"
pytest -k "not slow"

# Run by marker
pytest -m slow
pytest -m "not integration"
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `-v` | Verbose output |
| `-vv` | More verbose |
| `-s` | Show print statements (disable capture) |
| `-x` | Stop on first failure |
| `--maxfail=N` | Stop after N failures |
| `-q` | Quiet mode |
| `--lf` | Run last failed tests |
| `--ff` | Run failed tests first |
| `--nf` | Run new tests first |
| `--pdb` | Drop into debugger on failure |
| `--tb=short` | Shorter traceback |
| `--tb=no` | No traceback |
| `--collect-only` | Show what would run |

## Assertions

```python
# Basic assertions
assert result == expected
assert result != unexpected
assert result is None
assert result is not None
assert result in collection
assert result not in collection

# Boolean
assert condition
assert not condition

# Comparisons
assert value > 0
assert value >= minimum
assert value < maximum

# Approximate (for floats)
assert result == pytest.approx(expected, rel=1e-3)
assert result == pytest.approx(expected, abs=0.01)

# Collections
assert len(items) == 3
assert set(result) == {1, 2, 3}
assert result == [1, 2, 3]  # order matters
```

## Exception Testing

```python
import pytest

# Basic exception check
def test_raises_value_error():
    with pytest.raises(ValueError):
        raise ValueError("invalid")

# Check exception message
def test_raises_with_message():
    with pytest.raises(ValueError, match="invalid"):
        raise ValueError("invalid input")

# Access exception info
def test_exception_details():
    with pytest.raises(ValueError) as exc_info:
        raise ValueError("error message")
    assert "error" in str(exc_info.value)
    assert exc_info.type is ValueError

# Multiple exception types
def test_raises_multiple():
    with pytest.raises((ValueError, TypeError)):
        raise TypeError("wrong type")
```

## Warnings Testing

```python
import warnings
import pytest

def test_warning():
    with pytest.warns(UserWarning):
        warnings.warn("deprecated", UserWarning)

def test_warning_match():
    with pytest.warns(DeprecationWarning, match="old API"):
        warnings.warn("old API deprecated", DeprecationWarning)
```

## Configuration Files

### pytest.ini
```ini
[pytest]
testpaths = tests
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
filterwarnings =
    ignore::DeprecationWarning
```

### pyproject.toml
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
filterwarnings = ["ignore::DeprecationWarning"]
```

### conftest.py
- Shared fixtures and hooks
- Automatically discovered by pytest
- No import needed
- Can exist at multiple levels (project root, test directories)

## Output and Logging

```python
# Capture stdout/stderr
def test_output(capsys):
    print("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"
    assert captured.err == ""

# Capture logging
def test_logging(caplog):
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("alert!")
    assert "alert" in caplog.text
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"

# Set log level
def test_logging_level(caplog):
    with caplog.at_level(logging.DEBUG):
        logger.debug("debug message")
    assert "debug message" in caplog.text
```
