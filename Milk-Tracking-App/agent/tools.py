"""Tools for interacting with the Milk Tracking API.

This module provides function tools that the AI agent uses to interact with
the Milk Tracking backend API. Each tool handles authentication and API calls.
"""

import os
from datetime import date

import httpx
from agents import function_tool

# API Configuration from environment
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")
API_EMAIL = os.getenv("API_EMAIL", "")
API_PASSWORD = os.getenv("API_PASSWORD", "")

# Cache for JWT token
_token_cache: dict[str, str] = {}


async def get_auth_token() -> str:
    """Get JWT token for API authentication.

    Returns:
        str: JWT access token.

    Raises:
        Exception: If authentication fails.
    """
    if "token" in _token_cache:
        return _token_cache["token"]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/auth/token",
            data={"username": API_EMAIL, "password": API_PASSWORD},
        )
        if response.status_code != 200:
            raise Exception(f"Authentication failed: {response.text}")

        token_data = response.json()
        _token_cache["token"] = token_data["access_token"]
        return _token_cache["token"]


async def get_auth_headers() -> dict[str, str]:
    """Get authorization headers with JWT token.

    Returns:
        dict: Headers with Bearer token.
    """
    token = await get_auth_token()
    return {"Authorization": f"Bearer {token}"}


def clear_token_cache() -> None:
    """Clear the token cache to force re-authentication."""
    _token_cache.clear()


@function_tool
async def add_milk_entry(
    supplier_name: str, liters: float, entry_date: str | None = None
) -> str:
    """Add a milk entry for a supplier.

    Creates a new milk collection entry in the system. If no date is specified,
    uses today's date.

    Args:
        supplier_name: The name of the milk supplier.
        liters: Amount of milk in liters (must be positive).
        entry_date: Optional date in YYYY-MM-DD format. Uses today if not specified.

    Returns:
        Confirmation message with entry details.
    """
    try:
        headers = await get_auth_headers()

        # Use today's date if not specified
        if entry_date is None:
            entry_date = date.today().isoformat()

        payload = {
            "supplier_name": supplier_name,
            "liters": liters,
            "date": entry_date,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/entries/by-name",
                json=payload,
                headers=headers,
            )

            if response.status_code == 404:
                return f"Supplier '{supplier_name}' not found. Please check the name or add the supplier first."

            if response.status_code == 401:
                clear_token_cache()
                return "Authentication failed. Please check API credentials."

            response.raise_for_status()
            entry = response.json()

            return (
                f"Added milk entry:\n"
                f"- Supplier: {entry['supplier']['name']}\n"
                f"- Date: {entry['date']}\n"
                f"- Liters: {entry['liters']:.2f}\n"
                f"- Entry ID: {entry['id']}"
            )

    except httpx.HTTPError as e:
        return f"Error adding milk entry: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
async def list_entries(
    start_date: str | None = None, end_date: str | None = None
) -> str:
    """List milk entries with optional date filtering.

    Retrieves milk entries from the system. Can filter by date range.

    Args:
        start_date: Optional start date in YYYY-MM-DD format (inclusive).
        end_date: Optional end date in YYYY-MM-DD format (inclusive).

    Returns:
        Formatted list of milk entries with details.
    """
    try:
        headers = await get_auth_headers()

        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/entries",
                params=params,
                headers=headers,
            )

            if response.status_code == 401:
                clear_token_cache()
                return "Authentication failed. Please check API credentials."

            response.raise_for_status()
            entries = response.json()

            if not entries:
                date_range = ""
                if start_date or end_date:
                    date_range = f" between {start_date or 'start'} and {end_date or 'now'}"
                return f"No milk entries found{date_range}."

            result = f"Milk Entries ({len(entries)} total):\n"
            result += "-" * 50 + "\n"

            for entry in entries:
                supplier = entry.get("supplier", {})
                result += (
                    f"[{entry['date']}] {supplier.get('name', 'Unknown')}: "
                    f"{entry['liters']:.2f} liters "
                    f"({supplier.get('milk_type', 'unknown')} milk)\n"
                )

            return result

    except httpx.HTTPError as e:
        return f"Error listing entries: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
async def get_monthly_report(year: int, month: int) -> str:
    """Get monthly report with totals per supplier.

    Generates a comprehensive monthly report showing milk collection totals
    and payment amounts for each supplier.

    Args:
        year: The year for the report (e.g., 2024).
        month: The month for the report (1-12).

    Returns:
        Formatted monthly report with supplier totals and grand totals.
    """
    try:
        if month < 1 or month > 12:
            return "Invalid month. Please provide a month between 1 and 12."

        headers = await get_auth_headers()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/reports/monthly/{year}/{month}",
                headers=headers,
            )

            if response.status_code == 401:
                clear_token_cache()
                return "Authentication failed. Please check API credentials."

            response.raise_for_status()
            report = response.json()

            month_names = [
                "", "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            month_name = month_names[month]

            result = f"Monthly Milk Collection Report - {month_name} {year}\n"
            result += "=" * 60 + "\n\n"

            suppliers = report.get("suppliers", [])
            if not suppliers:
                result += "No entries found for this month.\n"
            else:
                result += f"{'Supplier':<20} {'Type':<10} {'Liters':>10} {'Rate':>8} {'Amount':>12}\n"
                result += "-" * 60 + "\n"

                for s in suppliers:
                    result += (
                        f"{s['supplier_name']:<20} "
                        f"{s['milk_type']:<10} "
                        f"{s['total_liters']:>10.2f} "
                        f"{s['rate_per_liter']:>8.2f} "
                        f"{s['total_amount']:>12.2f}\n"
                    )

                result += "-" * 60 + "\n"

            result += f"\nGrand Total: {report['grand_total_liters']:.2f} liters\n"
            result += f"Total Amount: Rs. {report['grand_total_amount']:.2f}\n"

            return result

    except httpx.HTTPError as e:
        return f"Error getting monthly report: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
async def list_suppliers() -> str:
    """List all active suppliers with their rates.

    Retrieves the list of all active milk suppliers in the system.

    Returns:
        Formatted list of suppliers with name, milk type, and rate per liter.
    """
    try:
        headers = await get_auth_headers()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/suppliers",
                headers=headers,
            )

            if response.status_code == 401:
                clear_token_cache()
                return "Authentication failed. Please check API credentials."

            response.raise_for_status()
            suppliers = response.json()

            if not suppliers:
                return "No active suppliers found."

            result = "Active Suppliers:\n"
            result += "-" * 50 + "\n"
            result += f"{'Name':<25} {'Type':<10} {'Rate/Liter':>12}\n"
            result += "-" * 50 + "\n"

            for supplier in suppliers:
                result += (
                    f"{supplier['name']:<25} "
                    f"{supplier['milk_type']:<10} "
                    f"Rs. {supplier['rate_per_liter']:>8.2f}\n"
                )

            return result

    except httpx.HTTPError as e:
        return f"Error listing suppliers: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
async def update_supplier_rate(supplier_name: str, new_rate: float) -> str:
    """Update a supplier's rate per liter.

    Changes the payment rate for milk from a specific supplier.

    Args:
        supplier_name: The name of the supplier to update.
        new_rate: The new rate per liter (must be positive).

    Returns:
        Confirmation message with updated supplier details.
    """
    try:
        if new_rate <= 0:
            return "Rate must be a positive number."

        headers = await get_auth_headers()

        async with httpx.AsyncClient() as client:
            # First, find the supplier by name
            response = await client.get(
                f"{API_BASE_URL}/api/v1/suppliers/by-name/{supplier_name}",
                headers=headers,
            )

            if response.status_code == 404:
                return f"Supplier '{supplier_name}' not found."

            if response.status_code == 401:
                clear_token_cache()
                return "Authentication failed. Please check API credentials."

            response.raise_for_status()
            supplier = response.json()
            old_rate = supplier["rate_per_liter"]

            # Update the supplier's rate
            update_response = await client.patch(
                f"{API_BASE_URL}/api/v1/suppliers/{supplier['id']}",
                json={"rate_per_liter": new_rate},
                headers=headers,
            )

            update_response.raise_for_status()
            updated = update_response.json()

            return (
                f"Updated supplier rate:\n"
                f"- Supplier: {updated['name']}\n"
                f"- Milk Type: {updated['milk_type']}\n"
                f"- Old Rate: Rs. {old_rate:.2f}/liter\n"
                f"- New Rate: Rs. {updated['rate_per_liter']:.2f}/liter"
            )

    except httpx.HTTPError as e:
        return f"Error updating supplier rate: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
async def add_supplier(name: str, milk_type: str, rate: float) -> str:
    """Add a new milk supplier.

    Creates a new supplier in the system.

    Args:
        name: The name of the supplier (1-100 characters).
        milk_type: Type of milk - must be either 'cow' or 'buffalo'.
        rate: Rate per liter (must be positive).

    Returns:
        Confirmation message with the new supplier's details.
    """
    try:
        # Validate milk type
        milk_type_lower = milk_type.lower().strip()
        if milk_type_lower not in ("cow", "buffalo"):
            return "Invalid milk type. Must be 'cow' or 'buffalo'."

        if rate <= 0:
            return "Rate must be a positive number."

        if not name or len(name) > 100:
            return "Supplier name must be between 1 and 100 characters."

        headers = await get_auth_headers()

        payload = {
            "name": name.strip(),
            "milk_type": milk_type_lower,
            "rate_per_liter": rate,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/suppliers",
                json=payload,
                headers=headers,
            )

            if response.status_code == 400:
                error_detail = response.json().get("detail", "Unknown error")
                return f"Could not add supplier: {error_detail}"

            if response.status_code == 401:
                clear_token_cache()
                return "Authentication failed. Please check API credentials."

            response.raise_for_status()
            supplier = response.json()

            return (
                f"Added new supplier:\n"
                f"- Name: {supplier['name']}\n"
                f"- Milk Type: {supplier['milk_type']}\n"
                f"- Rate: Rs. {supplier['rate_per_liter']:.2f}/liter\n"
                f"- Supplier ID: {supplier['id']}"
            )

    except httpx.HTTPError as e:
        return f"Error adding supplier: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
