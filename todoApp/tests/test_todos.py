"""Tests for Todo API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport


# =============================================================================
# Phase 1: Health Check Tests
# =============================================================================

class TestHealth:
    """Tests for health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self):
        """Health endpoint should return status healthy."""
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


# =============================================================================
# Phase 2: Configuration Tests
# =============================================================================

class TestConfig:
    """Tests for application configuration."""

    def test_settings_loads_database_url(self, monkeypatch):
        """Settings should load DATABASE_URL from environment."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/testdb")
        # Clear cached settings
        from app import config
        config.get_settings.cache_clear()

        from app.config import get_settings
        settings = get_settings()

        assert "postgresql+asyncpg" in settings.database_url

    def test_settings_has_debug_flag(self, monkeypatch):
        """Settings should have debug flag."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test@localhost/db")
        monkeypatch.setenv("DEBUG", "true")
        from app import config
        config.get_settings.cache_clear()

        from app.config import get_settings
        settings = get_settings()

        assert settings.debug is True


# =============================================================================
# Phase 3: Schema Tests
# =============================================================================

class TestTodoCreate:
    """Tests for TodoCreate schema."""

    def test_create_with_title_only(self):
        """Should create todo with just title."""
        from app.schemas import TodoCreate

        todo = TodoCreate(title="Test task")

        assert todo.title == "Test task"
        assert todo.description is None
        assert todo.completed is False

    def test_create_with_all_fields(self):
        """Should create todo with all fields."""
        from app.schemas import TodoCreate

        todo = TodoCreate(title="Test", description="Description", completed=True)

        assert todo.title == "Test"
        assert todo.description == "Description"
        assert todo.completed is True

    def test_create_requires_non_empty_title(self):
        """Should reject empty title."""
        from app.schemas import TodoCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TodoCreate(title="")


class TestTodoUpdate:
    """Tests for TodoUpdate schema."""

    def test_update_all_fields_optional(self):
        """All fields should be optional for updates."""
        from app.schemas import TodoUpdate

        update = TodoUpdate()

        assert update.title is None
        assert update.description is None
        assert update.completed is None

    def test_update_partial_fields(self):
        """Should allow partial updates."""
        from app.schemas import TodoUpdate

        update = TodoUpdate(completed=True)

        assert update.title is None
        assert update.completed is True


class TestTodoPublic:
    """Tests for TodoPublic schema."""

    def test_public_has_id(self):
        """Public schema should include id."""
        from app.schemas import TodoPublic

        todo = TodoPublic(id=1, title="Test", description=None, completed=False)

        assert todo.id == 1
        assert todo.title == "Test"


# =============================================================================
# Phase 5: CRUD Endpoint Tests
# =============================================================================

class TestCreateTodo:
    """Tests for POST /api/v1/todos endpoint."""

    @pytest.mark.asyncio
    async def test_create_todo_success(self, client: AsyncClient):
        """Should create a new todo."""
        response = await client.post(
            "/api/v1/todos",
            json={"title": "Buy groceries", "description": "Milk, eggs, bread"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert data["description"] == "Milk, eggs, bread"
        assert data["completed"] is False
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_todo_minimal(self, client: AsyncClient):
        """Should create todo with only title."""
        response = await client.post(
            "/api/v1/todos",
            json={"title": "Simple task"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Simple task"
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_todo_empty_title_fails(self, client: AsyncClient):
        """Should reject empty title."""
        response = await client.post(
            "/api/v1/todos",
            json={"title": ""}
        )

        assert response.status_code == 422


class TestListTodos:
    """Tests for GET /api/v1/todos endpoint."""

    @pytest.mark.asyncio
    async def test_list_todos_empty(self, client: AsyncClient):
        """Should return empty list when no todos exist."""
        response = await client.get("/api/v1/todos")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_todos_returns_all(self, client: AsyncClient):
        """Should return all todos."""
        # Create two todos
        await client.post("/api/v1/todos", json={"title": "Task 1"})
        await client.post("/api/v1/todos", json={"title": "Task 2"})

        response = await client.get("/api/v1/todos")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestGetTodo:
    """Tests for GET /api/v1/todos/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_todo_success(self, client: AsyncClient):
        """Should return a single todo by ID."""
        # Create a todo first
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": "Test task"}
        )
        todo_id = create_response.json()["id"]

        response = await client.get(f"/api/v1/todos/{todo_id}")

        assert response.status_code == 200
        assert response.json()["title"] == "Test task"

    @pytest.mark.asyncio
    async def test_get_todo_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent todo."""
        response = await client.get("/api/v1/todos/99999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Todo not found"


class TestUpdateTodo:
    """Tests for PATCH /api/v1/todos/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_todo_title(self, client: AsyncClient):
        """Should update todo title."""
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": "Original"}
        )
        todo_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"title": "Updated"}
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_todo_completed(self, client: AsyncClient):
        """Should update todo completed status."""
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": "Task"}
        )
        todo_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"completed": True}
        )

        assert response.status_code == 200
        assert response.json()["completed"] is True

    @pytest.mark.asyncio
    async def test_update_todo_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent todo."""
        response = await client.patch(
            "/api/v1/todos/99999",
            json={"title": "Updated"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_partial_preserves_other_fields(self, client: AsyncClient):
        """Should preserve fields not being updated."""
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": "Task", "description": "Important"}
        )
        todo_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"completed": True}
        )

        assert response.json()["description"] == "Important"
        assert response.json()["title"] == "Task"


class TestDeleteTodo:
    """Tests for DELETE /api/v1/todos/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_todo_success(self, client: AsyncClient):
        """Should delete a todo."""
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": "To delete"}
        )
        todo_id = create_response.json()["id"]

        response = await client.delete(f"/api/v1/todos/{todo_id}")

        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(f"/api/v1/todos/{todo_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_todo_not_found(self, client: AsyncClient):
        """Should return 404 for non-existent todo."""
        response = await client.delete("/api/v1/todos/99999")

        assert response.status_code == 404
