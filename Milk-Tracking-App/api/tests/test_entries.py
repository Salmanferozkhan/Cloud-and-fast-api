"""Tests for the MilkEntry module following TDD approach."""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


class TestEntryAuthentication:
    """Test cases for entry endpoint authentication requirements."""

    async def test_create_entry_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test creating entry without token returns 401."""
        response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": 1,
                "liters": 10.5,
            },
        )
        assert response.status_code == 401

    async def test_create_entry_by_name_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test creating entry by supplier name without token returns 401."""
        response = await client.post(
            "/api/v1/entries/by-name",
            json={
                "date": str(date.today()),
                "supplier_name": "Test Farm",
                "liters": 10.5,
            },
        )
        assert response.status_code == 401

    async def test_list_entries_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test listing entries without token returns 401."""
        response = await client.get("/api/v1/entries")
        assert response.status_code == 401

    async def test_get_entry_by_id_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test getting entry by ID without token returns 401."""
        response = await client.get("/api/v1/entries/1")
        assert response.status_code == 401

    async def test_update_entry_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test updating entry without token returns 401."""
        response = await client.patch(
            "/api/v1/entries/1",
            json={"liters": 15.0},
        )
        assert response.status_code == 401

    async def test_delete_entry_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test deleting entry without token returns 401."""
        response = await client.delete("/api/v1/entries/1")
        assert response.status_code == 401


class TestCreateEntry:
    """Test cases for entry creation endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "entry_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "entry_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def supplier_id(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> int:
        """Create a supplier and return its ID."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Entry Test Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        return response.json()["id"]

    async def test_create_entry_by_supplier_id_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test successful creation of milk entry by supplier ID."""
        today = date.today()
        response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(today),
                "supplier_id": supplier_id,
                "liters": 25.5,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["date"] == str(today)
        assert data["supplier_id"] == supplier_id
        assert data["liters"] == 25.5
        assert "id" in data
        assert "created_at" in data
        assert "supplier" in data
        assert data["supplier"]["name"] == "Entry Test Farm"

    async def test_create_entry_with_invalid_supplier_id_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating entry with non-existent supplier returns 404."""
        response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": 99999,
                "liters": 10.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "supplier" in response.json()["detail"].lower()

    async def test_create_entry_with_negative_liters_returns_422(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test creating entry with negative liters returns 422."""
        response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": supplier_id,
                "liters": -5.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_entry_with_zero_liters_returns_422(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test creating entry with zero liters returns 422."""
        response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": supplier_id,
                "liters": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_entry_missing_required_fields_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating entry with missing fields returns 422."""
        response = await client.post(
            "/api/v1/entries",
            json={"date": str(date.today())},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestCreateEntryByName:
    """Test cases for entry creation by supplier name endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "entry_byname_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "entry_byname_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def supplier_name(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> str:
        """Create a supplier and return its name."""
        await client.post(
            "/api/v1/suppliers",
            json={
                "name": "By Name Test Farm",
                "milk_type": "buffalo",
                "rate_per_liter": 70.0,
            },
            headers=auth_headers,
        )
        return "By Name Test Farm"

    async def test_create_entry_by_supplier_name_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_name: str,
    ) -> None:
        """Test successful creation of milk entry by supplier name."""
        today = date.today()
        response = await client.post(
            "/api/v1/entries/by-name",
            json={
                "date": str(today),
                "supplier_name": supplier_name,
                "liters": 30.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["date"] == str(today)
        assert data["liters"] == 30.0
        assert "id" in data
        assert "created_at" in data
        assert "supplier" in data
        assert data["supplier"]["name"] == supplier_name

    async def test_create_entry_by_name_with_invalid_supplier_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating entry with non-existent supplier name returns 404."""
        response = await client.post(
            "/api/v1/entries/by-name",
            json={
                "date": str(date.today()),
                "supplier_name": "Non Existent Farm",
                "liters": 10.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "supplier" in response.json()["detail"].lower()


class TestListEntries:
    """Test cases for listing entries endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "list_entries_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "list_entries_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def supplier_id(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> int:
        """Create a supplier and return its ID."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "List Entries Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        return response.json()["id"]

    async def test_list_entries_empty(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing entries when none exist returns empty list."""
        response = await client.get(
            "/api/v1/entries",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_entries_returns_all(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test listing entries returns all entries."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Create two entries
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(today),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(yesterday),
                "supplier_id": supplier_id,
                "liters": 25.0,
            },
            headers=auth_headers,
        )

        response = await client.get(
            "/api/v1/entries",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_list_entries_with_start_date_filter(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test listing entries with start_date filter."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        # Create entries for different dates
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(today),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(two_days_ago),
                "supplier_id": supplier_id,
                "liters": 25.0,
            },
            headers=auth_headers,
        )

        # Filter from yesterday (should only get today's entry)
        response = await client.get(
            f"/api/v1/entries?start_date={yesterday}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["date"] == str(today)

    async def test_list_entries_with_end_date_filter(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test listing entries with end_date filter."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        # Create entries for different dates
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(today),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(two_days_ago),
                "supplier_id": supplier_id,
                "liters": 25.0,
            },
            headers=auth_headers,
        )

        # Filter until yesterday (should only get two_days_ago entry)
        response = await client.get(
            f"/api/v1/entries?end_date={yesterday}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["date"] == str(two_days_ago)

    async def test_list_entries_with_date_range_filter(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test listing entries with both start_date and end_date filters."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        three_days_ago = today - timedelta(days=3)

        # Create entries for different dates
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(today),
                "supplier_id": supplier_id,
                "liters": 10.0,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(yesterday),
                "supplier_id": supplier_id,
                "liters": 15.0,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(three_days_ago),
                "supplier_id": supplier_id,
                "liters": 25.0,
            },
            headers=auth_headers,
        )

        # Filter between two_days_ago and today (should get yesterday's entry)
        response = await client.get(
            f"/api/v1/entries?start_date={two_days_ago}&end_date={yesterday}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["date"] == str(yesterday)

    async def test_list_entries_returns_all_fields(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test listing entries returns all expected fields."""
        await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )

        response = await client.get(
            "/api/v1/entries",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        entry = data[0]
        assert "id" in entry
        assert "date" in entry
        assert "supplier_id" in entry
        assert "liters" in entry
        assert "created_at" in entry
        assert "supplier" in entry
        assert "name" in entry["supplier"]


class TestGetEntryById:
    """Test cases for getting entry by ID endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "get_entry_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "get_entry_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def supplier_id(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> int:
        """Create a supplier and return its ID."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Get Entry Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        return response.json()["id"]

    async def test_get_entry_by_id_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test getting entry by valid ID."""
        today = date.today()
        create_response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(today),
                "supplier_id": supplier_id,
                "liters": 35.5,
            },
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/entries/{entry_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry_id
        assert data["date"] == str(today)
        assert data["supplier_id"] == supplier_id
        assert data["liters"] == 35.5
        assert "supplier" in data

    async def test_get_entry_by_id_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting entry with non-existent ID returns 404."""
        response = await client.get(
            "/api/v1/entries/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateEntry:
    """Test cases for updating entry endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "update_entry_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "update_entry_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def supplier_id(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> int:
        """Create a supplier and return its ID."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Update Entry Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        return response.json()["id"]

    @pytest.fixture
    async def second_supplier_id(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> int:
        """Create a second supplier and return its ID."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Second Update Entry Farm",
                "milk_type": "buffalo",
                "rate_per_liter": 70.0,
            },
            headers=auth_headers,
        )
        return response.json()["id"]

    async def test_update_entry_liters(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test updating entry liters."""
        create_response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/entries/{entry_id}",
            json={"liters": 25.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["liters"] == 25.0

    async def test_update_entry_date(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test updating entry date."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        create_response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(today),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/entries/{entry_id}",
            json={"date": str(yesterday)},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["date"] == str(yesterday)

    async def test_update_entry_supplier_id(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
        second_supplier_id: int,
    ) -> None:
        """Test updating entry supplier_id."""
        create_response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/entries/{entry_id}",
            json={"supplier_id": second_supplier_id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["supplier_id"] == second_supplier_id
        assert data["supplier"]["name"] == "Second Update Entry Farm"

    async def test_update_entry_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating non-existent entry returns 404."""
        response = await client.patch(
            "/api/v1/entries/99999",
            json={"liters": 25.0},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_update_entry_with_invalid_supplier_id_returns_404(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test updating entry with non-existent supplier_id returns 404."""
        create_response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/entries/{entry_id}",
            json={"supplier_id": 99999},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_update_entry_invalid_liters_returns_422(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test updating entry with invalid liters returns 422."""
        create_response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/entries/{entry_id}",
            json={"liters": -5.0},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestDeleteEntry:
    """Test cases for deleting entry endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "delete_entry_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "delete_entry_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    async def supplier_id(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> int:
        """Create a supplier and return its ID."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Delete Entry Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        return response.json()["id"]

    async def test_delete_entry_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        supplier_id: int,
    ) -> None:
        """Test deleting an entry."""
        create_response = await client.post(
            "/api/v1/entries",
            json={
                "date": str(date.today()),
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.delete(
            f"/api/v1/entries/{entry_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify entry is deleted
        get_response = await client.get(
            f"/api/v1/entries/{entry_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_entry_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test deleting non-existent entry returns 404."""
        response = await client.delete(
            "/api/v1/entries/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404
