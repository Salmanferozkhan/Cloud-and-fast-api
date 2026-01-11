"""Full integration tests for the Milk Tracking API.

This module tests the complete user flow from registration through
report generation, ensuring end-to-end functionality works correctly.
"""

import datetime as dt

import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self, client: AsyncClient) -> None:
        """Test that health endpoint returns 200 OK with healthy status.

        Args:
            client: Async HTTP client fixture.
        """
        response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestFullUserFlow:
    """Integration tests for the complete user flow.

    Tests the entire workflow:
    1. Register a new user
    2. Login to get access token
    3. Create a supplier
    4. Add milk entries
    5. Generate monthly report
    """

    @pytest.mark.asyncio
    async def test_complete_user_flow(self, client: AsyncClient) -> None:
        """Test the full user flow from registration to report generation.

        This test covers:
        - User registration
        - User login (token generation)
        - Supplier creation
        - Milk entry creation (by supplier ID)
        - Milk entry creation (by supplier name)
        - Monthly report generation with correct calculations

        Args:
            client: Async HTTP client fixture.
        """
        # Step 1: Register a new user
        registration_data = {
            "email": "integration@test.com",
            "password": "testpassword123",
        }
        response = await client.post("/api/v1/auth/register", json=registration_data)

        assert response.status_code == 201
        user_data = response.json()
        assert user_data["email"] == "integration@test.com"
        assert "id" in user_data
        assert "created_at" in user_data
        assert "password" not in user_data
        assert "hashed_password" not in user_data

        # Step 2: Login to get access token
        login_data = {
            "username": "integration@test.com",  # OAuth2 uses "username" field
            "password": "testpassword123",
        }
        response = await client.post("/api/v1/auth/token", data=login_data)

        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        access_token = token_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Step 3: Verify token works by getting current user
        response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        me_data = response.json()
        assert me_data["email"] == "integration@test.com"

        # Step 4: Create suppliers
        supplier1_data = {
            "name": "Green Valley Farm",
            "milk_type": "cow",
            "rate_per_liter": 55.50,
        }
        response = await client.post(
            "/api/v1/suppliers", json=supplier1_data, headers=auth_headers
        )

        assert response.status_code == 201
        supplier1 = response.json()
        assert supplier1["name"] == "Green Valley Farm"
        assert supplier1["milk_type"] == "cow"
        assert supplier1["rate_per_liter"] == 55.50
        assert supplier1["is_active"] is True
        supplier1_id = supplier1["id"]

        supplier2_data = {
            "name": "Buffalo Springs",
            "milk_type": "buffalo",
            "rate_per_liter": 75.00,
        }
        response = await client.post(
            "/api/v1/suppliers", json=supplier2_data, headers=auth_headers
        )

        assert response.status_code == 201
        supplier2 = response.json()
        assert supplier2["name"] == "Buffalo Springs"
        assert supplier2["milk_type"] == "buffalo"
        supplier2_id = supplier2["id"]

        # Step 5: Create milk entries by supplier ID
        today = dt.date.today()
        year = today.year
        month = today.month

        entry1_data = {
            "date": str(today),
            "supplier_id": supplier1_id,
            "liters": 25.5,
        }
        response = await client.post(
            "/api/v1/entries", json=entry1_data, headers=auth_headers
        )

        assert response.status_code == 201
        entry1 = response.json()
        assert entry1["liters"] == 25.5
        assert entry1["supplier_id"] == supplier1_id
        assert entry1["supplier"]["name"] == "Green Valley Farm"

        entry2_data = {
            "date": str(today),
            "supplier_id": supplier1_id,
            "liters": 30.0,
        }
        response = await client.post(
            "/api/v1/entries", json=entry2_data, headers=auth_headers
        )

        assert response.status_code == 201

        # Step 6: Create milk entry by supplier name
        entry3_data = {
            "date": str(today),
            "supplier_name": "Buffalo Springs",
            "liters": 40.0,
        }
        response = await client.post(
            "/api/v1/entries/by-name", json=entry3_data, headers=auth_headers
        )

        assert response.status_code == 201
        entry3 = response.json()
        assert entry3["liters"] == 40.0
        assert entry3["supplier"]["name"] == "Buffalo Springs"

        # Step 7: List all entries and verify count
        response = await client.get("/api/v1/entries", headers=auth_headers)

        assert response.status_code == 200
        entries = response.json()
        assert len(entries) == 3

        # Step 8: Get monthly report and verify calculations
        response = await client.get(
            f"/api/v1/reports/monthly/{year}/{month}", headers=auth_headers
        )

        assert response.status_code == 200
        report = response.json()

        assert report["year"] == year
        assert report["month"] == month
        assert len(report["suppliers"]) == 2

        # Find supplier reports by name
        supplier_reports = {s["supplier_name"]: s for s in report["suppliers"]}

        # Verify Green Valley Farm calculations (25.5 + 30.0 = 55.5 liters)
        gv_report = supplier_reports["Green Valley Farm"]
        assert gv_report["supplier_id"] == supplier1_id
        assert gv_report["milk_type"] == "cow"
        assert gv_report["rate_per_liter"] == 55.50
        assert gv_report["total_liters"] == 55.5
        assert gv_report["total_amount"] == 55.5 * 55.50  # 3080.25

        # Verify Buffalo Springs calculations (40.0 liters)
        bs_report = supplier_reports["Buffalo Springs"]
        assert bs_report["supplier_id"] == supplier2_id
        assert bs_report["milk_type"] == "buffalo"
        assert bs_report["rate_per_liter"] == 75.00
        assert bs_report["total_liters"] == 40.0
        assert bs_report["total_amount"] == 40.0 * 75.00  # 3000.00

        # Verify grand totals
        expected_grand_liters = 55.5 + 40.0  # 95.5
        expected_grand_amount = (55.5 * 55.50) + (40.0 * 75.00)  # 6080.25

        assert report["grand_total_liters"] == expected_grand_liters
        assert report["grand_total_amount"] == expected_grand_amount

    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, client: AsyncClient) -> None:
        """Test that protected endpoints require authentication.

        Args:
            client: Async HTTP client fixture.
        """
        # Try to access suppliers without authentication
        response = await client.get("/api/v1/suppliers")
        assert response.status_code == 401

        # Try to access entries without authentication
        response = await client.get("/api/v1/entries")
        assert response.status_code == 401

        # Try to access reports without authentication
        response = await client.get("/api/v1/reports/monthly/2024/1")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_credentials_rejected(self, client: AsyncClient) -> None:
        """Test that invalid login credentials are rejected.

        Args:
            client: Async HTTP client fixture.
        """
        # Register a user first
        registration_data = {
            "email": "credentials@test.com",
            "password": "correctpassword",
        }
        response = await client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 201

        # Try to login with wrong password
        login_data = {
            "username": "credentials@test.com",
            "password": "wrongpassword",
        }
        response = await client.post("/api/v1/auth/token", data=login_data)

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_duplicate_email_registration_rejected(
        self, client: AsyncClient
    ) -> None:
        """Test that duplicate email registration is rejected.

        Args:
            client: Async HTTP client fixture.
        """
        registration_data = {
            "email": "duplicate@test.com",
            "password": "password123",
        }

        # First registration should succeed
        response = await client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 201

        # Second registration with same email should fail
        response = await client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_supplier_crud_operations(self, client: AsyncClient) -> None:
        """Test supplier CRUD operations flow.

        Args:
            client: Async HTTP client fixture.
        """
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={"email": "crud@test.com", "password": "password123"},
        )
        token_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "crud@test.com", "password": "password123"},
        )
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create supplier
        response = await client.post(
            "/api/v1/suppliers",
            json={"name": "Test Farm", "milk_type": "cow", "rate_per_liter": 50.0},
            headers=headers,
        )
        assert response.status_code == 201
        supplier = response.json()
        supplier_id = supplier["id"]

        # Read supplier by ID
        response = await client.get(f"/api/v1/suppliers/{supplier_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Test Farm"

        # Read supplier by name
        response = await client.get(
            "/api/v1/suppliers/by-name/Test Farm", headers=headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == supplier_id

        # Update supplier
        response = await client.patch(
            f"/api/v1/suppliers/{supplier_id}",
            json={"rate_per_liter": 55.0},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["rate_per_liter"] == 55.0

        # List suppliers
        response = await client.get("/api/v1/suppliers", headers=headers)
        assert response.status_code == 200
        suppliers = response.json()
        assert len(suppliers) >= 1
        assert any(s["name"] == "Test Farm" for s in suppliers)

        # Delete (soft) supplier
        response = await client.delete(
            f"/api/v1/suppliers/{supplier_id}", headers=headers
        )
        assert response.status_code == 204

        # Verify supplier is no longer in active list
        response = await client.get("/api/v1/suppliers", headers=headers)
        suppliers = response.json()
        assert not any(s["id"] == supplier_id for s in suppliers)

    @pytest.mark.asyncio
    async def test_entry_crud_with_date_filtering(self, client: AsyncClient) -> None:
        """Test milk entry CRUD operations with date filtering.

        Args:
            client: Async HTTP client fixture.
        """
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={"email": "entries@test.com", "password": "password123"},
        )
        token_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "entries@test.com", "password": "password123"},
        )
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create supplier
        response = await client.post(
            "/api/v1/suppliers",
            json={"name": "Date Test Farm", "milk_type": "buffalo", "rate_per_liter": 70.0},
            headers=headers,
        )
        supplier_id = response.json()["id"]

        # Create entries on different dates
        today = dt.date.today()
        yesterday = today - dt.timedelta(days=1)
        two_days_ago = today - dt.timedelta(days=2)

        for date, liters in [(str(today), 10.0), (str(yesterday), 15.0), (str(two_days_ago), 20.0)]:
            await client.post(
                "/api/v1/entries",
                json={"date": date, "supplier_id": supplier_id, "liters": liters},
                headers=headers,
            )

        # List all entries
        response = await client.get("/api/v1/entries", headers=headers)
        assert len(response.json()) == 3

        # Filter by start_date
        response = await client.get(
            f"/api/v1/entries?start_date={yesterday}", headers=headers
        )
        entries = response.json()
        assert len(entries) == 2

        # Filter by end_date
        response = await client.get(
            f"/api/v1/entries?end_date={yesterday}", headers=headers
        )
        entries = response.json()
        assert len(entries) == 2

        # Filter by date range
        response = await client.get(
            f"/api/v1/entries?start_date={yesterday}&end_date={yesterday}",
            headers=headers,
        )
        entries = response.json()
        assert len(entries) == 1
        assert entries[0]["liters"] == 15.0

    @pytest.mark.asyncio
    async def test_report_empty_month(self, client: AsyncClient) -> None:
        """Test that monthly report works for months with no entries.

        Args:
            client: Async HTTP client fixture.
        """
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={"email": "emptyreport@test.com", "password": "password123"},
        )
        token_response = await client.post(
            "/api/v1/auth/token",
            data={"username": "emptyreport@test.com", "password": "password123"},
        )
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Request report for a month with no entries (January 2020)
        response = await client.get("/api/v1/reports/monthly/2020/1", headers=headers)

        assert response.status_code == 200
        report = response.json()
        assert report["year"] == 2020
        assert report["month"] == 1
        assert report["suppliers"] == []
        assert report["grand_total_liters"] == 0.0
        assert report["grand_total_amount"] == 0.0
