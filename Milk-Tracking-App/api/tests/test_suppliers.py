"""Tests for the Supplier module following TDD approach."""

import pytest
from httpx import AsyncClient


class TestSupplierAuthentication:
    """Test cases for supplier endpoint authentication requirements."""

    async def test_create_supplier_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test creating supplier without token returns 401."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Test Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
        )
        assert response.status_code == 401

    async def test_list_suppliers_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test listing suppliers without token returns 401."""
        response = await client.get("/api/v1/suppliers")
        assert response.status_code == 401

    async def test_get_supplier_by_id_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test getting supplier by ID without token returns 401."""
        response = await client.get("/api/v1/suppliers/1")
        assert response.status_code == 401

    async def test_get_supplier_by_name_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test getting supplier by name without token returns 401."""
        response = await client.get("/api/v1/suppliers/by-name/TestFarm")
        assert response.status_code == 401

    async def test_update_supplier_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test updating supplier without token returns 401."""
        response = await client.patch(
            "/api/v1/suppliers/1",
            json={"rate_per_liter": 55.0},
        )
        assert response.status_code == 401

    async def test_delete_supplier_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test deleting supplier without token returns 401."""
        response = await client.delete("/api/v1/suppliers/1")
        assert response.status_code == 401


class TestCreateSupplier:
    """Test cases for supplier creation endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "supplier_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "supplier_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_create_supplier_success_cow_milk(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test successful creation of cow milk supplier."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Happy Cow Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Happy Cow Farm"
        assert data["milk_type"] == "cow"
        assert data["rate_per_liter"] == 50.0
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    async def test_create_supplier_success_buffalo_milk(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test successful creation of buffalo milk supplier."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Buffalo Valley",
                "milk_type": "buffalo",
                "rate_per_liter": 70.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Buffalo Valley"
        assert data["milk_type"] == "buffalo"
        assert data["rate_per_liter"] == 70.0
        assert data["is_active"] is True

    async def test_create_supplier_duplicate_name_returns_400(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating supplier with duplicate name returns 400."""
        supplier_data = {
            "name": "Duplicate Farm",
            "milk_type": "cow",
            "rate_per_liter": 50.0,
        }
        # Create first supplier
        response = await client.post(
            "/api/v1/suppliers",
            json=supplier_data,
            headers=auth_headers,
        )
        assert response.status_code == 201

        # Try to create supplier with same name
        response = await client.post(
            "/api/v1/suppliers",
            json=supplier_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_supplier_invalid_milk_type_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating supplier with invalid milk type returns 422."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Invalid Farm",
                "milk_type": "goat",  # Invalid type
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_supplier_negative_rate_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating supplier with negative rate returns 422."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Negative Rate Farm",
                "milk_type": "cow",
                "rate_per_liter": -10.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_supplier_zero_rate_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating supplier with zero rate returns 422."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Zero Rate Farm",
                "milk_type": "cow",
                "rate_per_liter": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_supplier_empty_name_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating supplier with empty name returns 422."""
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_supplier_missing_required_fields_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating supplier with missing fields returns 422."""
        response = await client.post(
            "/api/v1/suppliers",
            json={"name": "Incomplete Farm"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestListSuppliers:
    """Test cases for listing suppliers endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "list_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "list_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_list_suppliers_empty(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing suppliers when none exist returns empty list."""
        response = await client.get(
            "/api/v1/suppliers",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_suppliers_returns_active_only(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing suppliers returns only active suppliers."""
        # Create two suppliers
        await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Active Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "To Be Deleted Farm",
                "milk_type": "buffalo",
                "rate_per_liter": 70.0,
            },
            headers=auth_headers,
        )
        supplier_id = response.json()["id"]

        # Soft-delete second supplier
        await client.delete(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )

        # List should only return active supplier
        response = await client.get(
            "/api/v1/suppliers",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active Farm"

    async def test_list_suppliers_returns_all_fields(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing suppliers returns all expected fields."""
        await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Complete Farm",
                "milk_type": "cow",
                "rate_per_liter": 55.5,
            },
            headers=auth_headers,
        )

        response = await client.get(
            "/api/v1/suppliers",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        supplier = data[0]
        assert "id" in supplier
        assert "name" in supplier
        assert "milk_type" in supplier
        assert "rate_per_liter" in supplier
        assert "is_active" in supplier
        assert "created_at" in supplier


class TestGetSupplierById:
    """Test cases for getting supplier by ID endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "getbyid_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "getbyid_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_get_supplier_by_id_success(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting supplier by valid ID."""
        # Create supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Findable Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        # Get by ID
        response = await client.get(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == supplier_id
        assert data["name"] == "Findable Farm"
        assert data["milk_type"] == "cow"
        assert data["rate_per_liter"] == 50.0

    async def test_get_supplier_by_id_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting supplier with non-existent ID returns 404."""
        response = await client.get(
            "/api/v1/suppliers/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_inactive_supplier_by_id_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting soft-deleted supplier returns 404."""
        # Create and delete supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Deleted Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        await client.delete(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )

        # Try to get deleted supplier
        response = await client.get(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGetSupplierByName:
    """Test cases for getting supplier by name endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "getbyname_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "getbyname_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_get_supplier_by_name_success(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting supplier by name."""
        # Create supplier
        await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Named Farm",
                "milk_type": "buffalo",
                "rate_per_liter": 70.0,
            },
            headers=auth_headers,
        )

        # Get by name
        response = await client.get(
            "/api/v1/suppliers/by-name/Named Farm",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Named Farm"
        assert data["milk_type"] == "buffalo"
        assert data["rate_per_liter"] == 70.0

    async def test_get_supplier_by_name_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting supplier with non-existent name returns 404."""
        response = await client.get(
            "/api/v1/suppliers/by-name/NonExistent Farm",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_inactive_supplier_by_name_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting soft-deleted supplier by name returns 404."""
        # Create supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Deleted Named Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        # Delete supplier
        await client.delete(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )

        # Try to get by name
        response = await client.get(
            "/api/v1/suppliers/by-name/Deleted Named Farm",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestUpdateSupplier:
    """Test cases for updating supplier endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "update_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "update_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_update_supplier_rate(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating supplier rate."""
        # Create supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Updatable Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        # Update rate
        response = await client.patch(
            f"/api/v1/suppliers/{supplier_id}",
            json={"rate_per_liter": 55.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rate_per_liter"] == 55.0
        assert data["name"] == "Updatable Farm"  # Unchanged

    async def test_update_supplier_name(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating supplier name."""
        # Create supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Old Name Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        # Update name
        response = await client.patch(
            f"/api/v1/suppliers/{supplier_id}",
            json={"name": "New Name Farm"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name Farm"

    async def test_update_supplier_milk_type(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating supplier milk type."""
        # Create supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Type Change Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        # Update milk type
        response = await client.patch(
            f"/api/v1/suppliers/{supplier_id}",
            json={"milk_type": "buffalo"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["milk_type"] == "buffalo"

    async def test_update_supplier_reactivate(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test reactivating a soft-deleted supplier."""
        # Create and delete supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Reactivate Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        await client.delete(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )

        # Reactivate
        response = await client.patch(
            f"/api/v1/suppliers/{supplier_id}",
            json={"is_active": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    async def test_update_supplier_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating non-existent supplier returns 404."""
        response = await client.patch(
            "/api/v1/suppliers/99999",
            json={"rate_per_liter": 55.0},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_update_supplier_duplicate_name_returns_400(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating supplier with existing name returns 400."""
        # Create two suppliers
        await client.post(
            "/api/v1/suppliers",
            json={
                "name": "First Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Second Farm",
                "milk_type": "buffalo",
                "rate_per_liter": 70.0,
            },
            headers=auth_headers,
        )
        second_id = create_response.json()["id"]

        # Try to update second supplier with first supplier's name
        response = await client.patch(
            f"/api/v1/suppliers/{second_id}",
            json={"name": "First Farm"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_update_supplier_invalid_rate_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating supplier with invalid rate returns 422."""
        # Create supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Invalid Rate Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        # Try to update with negative rate
        response = await client.patch(
            f"/api/v1/suppliers/{supplier_id}",
            json={"rate_per_liter": -10.0},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestDeleteSupplier:
    """Test cases for soft-deleting supplier endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "delete_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "delete_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_delete_supplier_success(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test soft-deleting a supplier."""
        # Create supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Deletable Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        # Delete supplier
        response = await client.delete(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify supplier is no longer accessible
        get_response = await client.get(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_supplier_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test deleting non-existent supplier returns 404."""
        response = await client.delete(
            "/api/v1/suppliers/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_already_deleted_supplier_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test deleting already deleted supplier returns 404."""
        # Create and delete supplier
        create_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Double Delete Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = create_response.json()["id"]

        await client.delete(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )

        # Try to delete again
        response = await client.delete(
            f"/api/v1/suppliers/{supplier_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
