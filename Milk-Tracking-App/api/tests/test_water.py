"""Tests for the WaterEntry module following TDD approach."""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


class TestWaterAuthentication:
    """Test cases for water endpoint authentication requirements."""

    async def test_create_water_entry_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test creating water entry without token returns 401."""
        response = await client.post(
            "/api/v1/water",
            json={
                "date": str(date.today()),
                "bottles": 5,
            },
        )
        assert response.status_code == 401

    async def test_list_water_entries_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test listing water entries without token returns 401."""
        response = await client.get("/api/v1/water")
        assert response.status_code == 401

    async def test_get_water_entry_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test getting water entry without token returns 401."""
        response = await client.get("/api/v1/water/1")
        assert response.status_code == 401

    async def test_update_water_entry_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test updating water entry without token returns 401."""
        response = await client.patch(
            "/api/v1/water/1",
            json={"bottles": 10},
        )
        assert response.status_code == 401

    async def test_delete_water_entry_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test deleting water entry without token returns 401."""
        response = await client.delete("/api/v1/water/1")
        assert response.status_code == 401

    async def test_monthly_water_report_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test getting monthly water report without token returns 401."""
        response = await client.get("/api/v1/water/reports/monthly/2024/1")
        assert response.status_code == 401


class TestCreateWaterEntry:
    """Test cases for water entry creation endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "water_create_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "water_create_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_create_water_entry_with_explicit_rate_success(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test successful creation of water entry with explicit rate_per_bottle."""
        today = date.today()
        response = await client.post(
            "/api/v1/water",
            json={
                "date": str(today),
                "bottles": 5,
                "rate_per_bottle": 100.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["date"] == str(today)
        assert data["bottles"] == 5
        assert data["rate_per_bottle"] == 100.0
        assert "id" in data
        assert "created_at" in data

    async def test_create_water_entry_without_rate_defaults_to_80(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating water entry without rate_per_bottle defaults to 80.0."""
        today = date.today()
        response = await client.post(
            "/api/v1/water",
            json={
                "date": str(today),
                "bottles": 3,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["bottles"] == 3
        assert data["rate_per_bottle"] == 80.0

    async def test_create_water_entry_with_zero_bottles_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating water entry with zero bottles returns 422."""
        response = await client.post(
            "/api/v1/water",
            json={
                "date": str(date.today()),
                "bottles": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_water_entry_with_negative_bottles_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating water entry with negative bottles returns 422."""
        response = await client.post(
            "/api/v1/water",
            json={
                "date": str(date.today()),
                "bottles": -2,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_water_entry_with_zero_rate_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating water entry with zero rate returns 422."""
        response = await client.post(
            "/api/v1/water",
            json={
                "date": str(date.today()),
                "bottles": 5,
                "rate_per_bottle": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_water_entry_missing_required_fields_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating water entry with missing fields returns 422."""
        response = await client.post(
            "/api/v1/water",
            json={"date": str(date.today())},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestListWaterEntries:
    """Test cases for listing water entries endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "water_list_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "water_list_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_list_water_entries_empty(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing water entries when none exist returns empty list."""
        response = await client.get("/api/v1/water", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_water_entries_returns_all_ordered_desc(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing water entries returns all entries ordered by date desc."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        await client.post(
            "/api/v1/water",
            json={"date": str(yesterday), "bottles": 3},
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/water",
            json={"date": str(today), "bottles": 5},
            headers=auth_headers,
        )

        response = await client.get("/api/v1/water", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["date"] == str(today)
        assert data[1]["date"] == str(yesterday)

    async def test_list_water_entries_with_date_range_filter(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing water entries with date range filter."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        three_days_ago = today - timedelta(days=3)

        await client.post(
            "/api/v1/water",
            json={"date": str(today), "bottles": 1},
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/water",
            json={"date": str(yesterday), "bottles": 2},
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/water",
            json={"date": str(three_days_ago), "bottles": 4},
            headers=auth_headers,
        )

        response = await client.get(
            f"/api/v1/water?start_date={two_days_ago}&end_date={yesterday}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["date"] == str(yesterday)


class TestGetWaterEntryById:
    """Test cases for getting water entry by ID endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "water_get_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "water_get_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_get_water_entry_by_id_success(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting water entry by valid ID."""
        today = date.today()
        create_response = await client.post(
            "/api/v1/water",
            json={"date": str(today), "bottles": 7, "rate_per_bottle": 90.0},
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/water/{entry_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry_id
        assert data["bottles"] == 7
        assert data["rate_per_bottle"] == 90.0

    async def test_get_water_entry_by_id_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting water entry with non-existent ID returns 404."""
        response = await client.get("/api/v1/water/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateWaterEntry:
    """Test cases for updating water entry endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "water_update_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "water_update_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_update_water_entry_bottles(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test partial update of water entry bottles only."""
        create_response = await client.post(
            "/api/v1/water",
            json={"date": str(date.today()), "bottles": 5},
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/water/{entry_id}",
            json={"bottles": 12},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bottles"] == 12
        assert data["rate_per_bottle"] == 80.0  # unchanged

    async def test_update_water_entry_rate(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test partial update of water entry rate only."""
        create_response = await client.post(
            "/api/v1/water",
            json={"date": str(date.today()), "bottles": 5},
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/water/{entry_id}",
            json={"rate_per_bottle": 120.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rate_per_bottle"] == 120.0
        assert data["bottles"] == 5  # unchanged

    async def test_update_water_entry_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating non-existent water entry returns 404."""
        response = await client.patch(
            "/api/v1/water/99999",
            json={"bottles": 3},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_update_water_entry_invalid_bottles_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating water entry with invalid bottles returns 422."""
        create_response = await client.post(
            "/api/v1/water",
            json={"date": str(date.today()), "bottles": 5},
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        response = await client.patch(
            f"/api/v1/water/{entry_id}",
            json={"bottles": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestDeleteWaterEntry:
    """Test cases for deleting water entry endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "water_delete_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "water_delete_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_delete_water_entry_then_get_returns_404(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test deleting water entry then fetching returns 404."""
        create_response = await client.post(
            "/api/v1/water",
            json={"date": str(date.today()), "bottles": 4},
            headers=auth_headers,
        )
        entry_id = create_response.json()["id"]

        delete_response = await client.delete(
            f"/api/v1/water/{entry_id}", headers=auth_headers
        )
        assert delete_response.status_code == 204

        get_response = await client.get(
            f"/api/v1/water/{entry_id}", headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_delete_water_entry_not_found(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test deleting non-existent water entry returns 404."""
        response = await client.delete(
            "/api/v1/water/99999", headers=auth_headers
        )
        assert response.status_code == 404


class TestMonthlyWaterReport:
    """Test cases for monthly water bottle report endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "water_report_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "water_report_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_monthly_report_no_entries_returns_zeros(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report with no entries returns zero totals."""
        response = await client.get(
            "/api/v1/water/reports/monthly/2024/1",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2024
        assert data["month"] == 1
        assert data["total_bottles"] == 0
        assert data["total_amount"] == 0.0
        assert data["entry_count"] == 0
        assert data["rate_per_bottle_avg"] == 0.0

    async def test_monthly_report_mixed_rate_entries(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report aggregates entries with different rates correctly."""
        # Entry 1: 5 bottles @ 80.0 = 400.0
        await client.post(
            "/api/v1/water",
            json={
                "date": "2024-03-05",
                "bottles": 5,
                "rate_per_bottle": 80.0,
            },
            headers=auth_headers,
        )
        # Entry 2: 10 bottles @ 100.0 = 1000.0
        await client.post(
            "/api/v1/water",
            json={
                "date": "2024-03-15",
                "bottles": 10,
                "rate_per_bottle": 100.0,
            },
            headers=auth_headers,
        )
        # Entry 3: 5 bottles @ 120.0 = 600.0
        await client.post(
            "/api/v1/water",
            json={
                "date": "2024-03-25",
                "bottles": 5,
                "rate_per_bottle": 120.0,
            },
            headers=auth_headers,
        )

        response = await client.get(
            "/api/v1/water/reports/monthly/2024/3",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["year"] == 2024
        assert data["month"] == 3
        assert data["total_bottles"] == 20  # 5 + 10 + 5
        assert data["total_amount"] == 2000.0  # 400 + 1000 + 600
        assert data["entry_count"] == 3
        # Weighted avg = 2000.0 / 20 = 100.0
        assert data["rate_per_bottle_avg"] == 100.0

    async def test_monthly_report_filters_by_month_and_year(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report only includes entries from specified month/year."""
        # In-month entry
        await client.post(
            "/api/v1/water",
            json={"date": "2024-04-10", "bottles": 5, "rate_per_bottle": 80.0},
            headers=auth_headers,
        )
        # Different month
        await client.post(
            "/api/v1/water",
            json={"date": "2024-05-10", "bottles": 7, "rate_per_bottle": 80.0},
            headers=auth_headers,
        )
        # Different year
        await client.post(
            "/api/v1/water",
            json={"date": "2023-04-10", "bottles": 9, "rate_per_bottle": 80.0},
            headers=auth_headers,
        )

        response = await client.get(
            "/api/v1/water/reports/monthly/2024/4",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_bottles"] == 5
        assert data["entry_count"] == 1
        assert data["total_amount"] == 400.0

    async def test_monthly_report_invalid_month_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report with invalid month returns 422."""
        response = await client.get(
            "/api/v1/water/reports/monthly/2024/13",
            headers=auth_headers,
        )
        assert response.status_code == 422

        response = await client.get(
            "/api/v1/water/reports/monthly/2024/0",
            headers=auth_headers,
        )
        assert response.status_code == 422
