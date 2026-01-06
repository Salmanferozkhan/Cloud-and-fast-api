# Pytest Mocking Reference

## monkeypatch (Built-in)

### Patching Attributes
```python
def test_patch_attribute(monkeypatch):
    # Patch module attribute
    monkeypatch.setattr("module.CONSTANT", 42)

    # Patch object attribute
    monkeypatch.setattr(obj, "attribute", "new_value")

    # Patch method
    monkeypatch.setattr(MyClass, "method", lambda self: "mocked")

    # Patch with callable
    def mock_function(*args, **kwargs):
        return "mocked result"
    monkeypatch.setattr("module.function", mock_function)
```

### Environment Variables
```python
def test_env_vars(monkeypatch):
    # Set env var
    monkeypatch.setenv("API_KEY", "test-key-123")
    monkeypatch.setenv("DEBUG", "true")

    # Delete env var
    monkeypatch.delenv("SECRET", raising=False)

    # Now test code that uses these env vars
    assert os.getenv("API_KEY") == "test-key-123"
```

### Dictionary Items
```python
def test_dict_patch(monkeypatch):
    config = {"timeout": 30, "retries": 3}

    monkeypatch.setitem(config, "timeout", 5)
    monkeypatch.delitem(config, "retries")

    assert config["timeout"] == 5
    assert "retries" not in config
```

### Changing Directories
```python
def test_chdir(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert Path.cwd() == tmp_path
```

### Patching sys.path
```python
def test_sys_path(monkeypatch):
    monkeypatch.syspath_prepend("/custom/path")
    assert sys.path[0] == "/custom/path"
```

## pytest-mock Plugin

Install: `pip install pytest-mock`

### Basic Usage
```python
def test_with_mocker(mocker):
    # Create a mock
    mock_func = mocker.patch("module.function")
    mock_func.return_value = "mocked"

    result = module.function()
    assert result == "mocked"
    mock_func.assert_called_once()
```

### Mock Return Values
```python
def test_return_values(mocker):
    mock = mocker.patch("module.get_data")

    # Single return value
    mock.return_value = {"key": "value"}

    # Multiple return values
    mock.side_effect = [1, 2, 3]

    # Raise exception
    mock.side_effect = ValueError("error")

    # Dynamic return based on input
    mock.side_effect = lambda x: x * 2
```

### Mock Assertions
```python
def test_assertions(mocker):
    mock = mocker.patch("module.send_email")

    # Call the code
    notify_user("test@example.com", "Hello")

    # Assert called
    mock.assert_called()
    mock.assert_called_once()
    mock.assert_called_with("test@example.com", "Hello")
    mock.assert_called_once_with("test@example.com", "Hello")

    # Check call count
    assert mock.call_count == 1

    # Check call args
    args, kwargs = mock.call_args
    assert args[0] == "test@example.com"

    # Not called
    mock.assert_not_called()
```

### Spy (Track Real Calls)
```python
def test_spy(mocker):
    # Spy tracks calls but executes real function
    spy = mocker.spy(module, "real_function")

    result = module.real_function(42)

    # Real function executed
    assert result == expected_real_result

    # But we can check it was called
    spy.assert_called_once_with(42)
```

### Mock Objects
```python
def test_mock_object(mocker):
    # Create mock with spec
    mock_db = mocker.Mock(spec=Database)
    mock_db.query.return_value = [{"id": 1}]

    # Use in test
    result = service.get_items(mock_db)
    mock_db.query.assert_called_with("SELECT * FROM items")

    # MagicMock for magic methods
    mock_file = mocker.MagicMock()
    mock_file.__enter__.return_value = mock_file
    mock_file.read.return_value = "content"
```

### Property Mocks
```python
def test_property(mocker):
    mock_property = mocker.PropertyMock(return_value="mocked")
    mocker.patch.object(MyClass, "my_property", mock_property)

    obj = MyClass()
    assert obj.my_property == "mocked"
```

### Async Mocks
```python
import pytest

@pytest.mark.asyncio
async def test_async(mocker):
    # Mock async function
    mock_fetch = mocker.patch("module.fetch_data")
    mock_fetch.return_value = {"data": "value"}

    # Or use AsyncMock
    mock_async = mocker.AsyncMock(return_value={"data": "value"})
    mocker.patch("module.async_func", mock_async)

    result = await module.async_func()
    mock_async.assert_awaited_once()
```

### Context Managers
```python
def test_context_manager(mocker):
    mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="file content"))

    with open("test.txt") as f:
        content = f.read()

    assert content == "file content"
    mock_open.assert_called_with("test.txt")
```

### Patching Classes
```python
def test_patch_class(mocker):
    # Patch class instantiation
    MockClass = mocker.patch("module.SomeClass")
    mock_instance = MockClass.return_value
    mock_instance.method.return_value = "result"

    obj = module.SomeClass()
    result = obj.method()

    assert result == "result"
```

## unittest.mock (Standard Library)

```python
from unittest.mock import Mock, patch, MagicMock

def test_with_patch():
    with patch("module.function") as mock:
        mock.return_value = "mocked"
        result = module.function()
    assert result == "mocked"

@patch("module.function")
def test_decorator(mock_func):
    mock_func.return_value = "mocked"
    result = module.function()
    assert result == "mocked"

# Multiple patches
@patch("module.func1")
@patch("module.func2")
def test_multiple(mock_func2, mock_func1):  # Note: reverse order
    pass
```

## Mocking Best Practices

1. **Mock at the right level** - Mock where it's used, not where defined
2. **Use spec** - `Mock(spec=RealClass)` catches attribute errors
3. **Prefer dependency injection** - Pass dependencies instead of patching
4. **Don't over-mock** - Test real behavior when possible
5. **Reset mocks between tests** - Use fixtures for isolation
6. **Mock external services** - APIs, databases, file systems
7. **Use spies for verification** - When you need real behavior + assertions
