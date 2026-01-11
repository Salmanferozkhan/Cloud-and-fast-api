"""Tests for the Reports module following TDD approach."""

from datetime import date

import pytest
from httpx import AsyncClient


class TestReportAuthentication:
    """Test cases for report endpoint authentication requirements."""

    async def test_get_monthly_report_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test getting monthly report without token returns 401."""
        response = await client.get("/api/v1/reports/monthly/2024/1")
        assert response.status_code == 401


class TestGetMonthlyReport:
    """Test cases for monthly report endpoint."""

    @pytest.fixture
    async def auth_headers(self, client: AsyncClient) -> dict[str, str]:
        """Register and login a user, return auth headers."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "report_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "report_test@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_monthly_report_with_no_entries_returns_empty_list(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report with no entries returns empty suppliers list."""
        response = await client.get(
            "/api/v1/reports/monthly/2024/1",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2024
        assert data["month"] == 1
        assert data["suppliers"] == []
        assert data["grand_total_liters"] == 0.0
        assert data["grand_total_amount"] == 0.0

    async def test_monthly_report_includes_supplier_details_with_totals(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report includes supplier details with calculated totals."""
        # Create a supplier
        supplier_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Report Test Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = supplier_response.json()["id"]

        # Create entries for January 2024
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-01-15",
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-01-20",
                "supplier_id": supplier_id,
                "liters": 30.0,
            },
            headers=auth_headers,
        )

        # Get monthly report
        response = await client.get(
            "/api/v1/reports/monthly/2024/1",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["year"] == 2024
        assert data["month"] == 1
        assert len(data["suppliers"]) == 1

        supplier_report = data["suppliers"][0]
        assert supplier_report["supplier_id"] == supplier_id
        assert supplier_report["supplier_name"] == "Report Test Farm"
        assert supplier_report["milk_type"] == "cow"
        assert supplier_report["rate_per_liter"] == 50.0
        assert supplier_report["total_liters"] == 50.0  # 20 + 30

    async def test_monthly_report_calculates_amount_correctly(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report calculates total_amount as total_liters * rate_per_liter."""
        # Create a supplier with specific rate
        supplier_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Amount Calc Farm",
                "milk_type": "buffalo",
                "rate_per_liter": 70.0,
            },
            headers=auth_headers,
        )
        supplier_id = supplier_response.json()["id"]

        # Create entries totaling 100 liters
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-02-10",
                "supplier_id": supplier_id,
                "liters": 40.0,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-02-15",
                "supplier_id": supplier_id,
                "liters": 60.0,
            },
            headers=auth_headers,
        )

        # Get monthly report
        response = await client.get(
            "/api/v1/reports/monthly/2024/2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        supplier_report = data["suppliers"][0]
        assert supplier_report["total_liters"] == 100.0
        # total_amount = 100 liters * 70.0 rate = 7000.0
        assert supplier_report["total_amount"] == 7000.0

    async def test_monthly_report_grand_totals(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report calculates grand totals across all suppliers."""
        # Create two suppliers
        supplier1_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Grand Total Farm 1",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier1_id = supplier1_response.json()["id"]

        supplier2_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Grand Total Farm 2",
                "milk_type": "buffalo",
                "rate_per_liter": 80.0,
            },
            headers=auth_headers,
        )
        supplier2_id = supplier2_response.json()["id"]

        # Create entries for supplier 1 (50 liters @ 50.0 = 2500.0)
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-03-10",
                "supplier_id": supplier1_id,
                "liters": 50.0,
            },
            headers=auth_headers,
        )

        # Create entries for supplier 2 (30 liters @ 80.0 = 2400.0)
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-03-15",
                "supplier_id": supplier2_id,
                "liters": 30.0,
            },
            headers=auth_headers,
        )

        # Get monthly report
        response = await client.get(
            "/api/v1/reports/monthly/2024/3",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["suppliers"]) == 2
        assert data["grand_total_liters"] == 80.0  # 50 + 30
        assert data["grand_total_amount"] == 4900.0  # 2500 + 2400

    async def test_monthly_report_filters_by_month(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report only includes entries from the specified month."""
        # Create a supplier
        supplier_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Month Filter Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = supplier_response.json()["id"]

        # Create entries for different months
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-04-15",
                "supplier_id": supplier_id,
                "liters": 25.0,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-05-15",
                "supplier_id": supplier_id,
                "liters": 35.0,
            },
            headers=auth_headers,
        )

        # Get report for April only
        response = await client.get(
            "/api/v1/reports/monthly/2024/4",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["suppliers"]) == 1
        assert data["suppliers"][0]["total_liters"] == 25.0

        # Get report for May only
        response = await client.get(
            "/api/v1/reports/monthly/2024/5",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["suppliers"]) == 1
        assert data["suppliers"][0]["total_liters"] == 35.0

    async def test_monthly_report_filters_by_year(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report only includes entries from the specified year."""
        # Create a supplier
        supplier_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Year Filter Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = supplier_response.json()["id"]

        # Create entries for different years
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-06-15",
                "supplier_id": supplier_id,
                "liters": 20.0,
            },
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2023-06-15",
                "supplier_id": supplier_id,
                "liters": 40.0,
            },
            headers=auth_headers,
        )

        # Get report for June 2024
        response = await client.get(
            "/api/v1/reports/monthly/2024/6",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["grand_total_liters"] == 20.0

        # Get report for June 2023
        response = await client.get(
            "/api/v1/reports/monthly/2023/6",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["grand_total_liters"] == 40.0

    async def test_monthly_report_invalid_month_returns_422(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report with invalid month returns 422."""
        # Month 13 is invalid
        response = await client.get(
            "/api/v1/reports/monthly/2024/13",
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Month 0 is invalid
        response = await client.get(
            "/api/v1/reports/monthly/2024/0",
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_monthly_report_excludes_inactive_suppliers(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test monthly report excludes entries from inactive suppliers."""
        # Create a supplier
        supplier_response = await client.post(
            "/api/v1/suppliers",
            json={
                "name": "Inactive Test Farm",
                "milk_type": "cow",
                "rate_per_liter": 50.0,
            },
            headers=auth_headers,
        )
        supplier_id = supplier_response.json()["id"]

        # Create entries
        await client.post(
            "/api/v1/entries",
            json={
                "date": "2024-07-15",
                "supplier_id": supplier_id,
                "liters": 25.0,
            },
            headers=auth_headers,
        )

        # Deactivate the supplier
        await client.patch(
            f"/api/v1/suppliers/{supplier_id}",
            json={"is_active": False},
            headers=auth_headers,
        )

        # Get monthly report - should not include inactive supplier
        response = await client.get(
            "/api/v1/reports/monthly/2024/7",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert len(data["suppliers"]) == 0
        assert data["grand_total_liters"] == 0.0
        assert data["grand_total_amount"] == 0.0
