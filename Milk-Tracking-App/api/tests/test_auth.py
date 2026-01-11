"""Tests for the authentication module following TDD approach."""

import pytest
from httpx import AsyncClient


class TestUserRegistration:
    """Test cases for user registration endpoint."""

    async def test_register_user_success(self, client: AsyncClient) -> None:
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_user_duplicate_email(self, client: AsyncClient) -> None:
        """Test registration fails with duplicate email."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePassword123!",
        }
        # Register first user
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        # Try to register with same email
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_user_invalid_email(self, client: AsyncClient) -> None:
        """Test registration fails with invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePassword123!",
            },
        )
        assert response.status_code == 422

    async def test_register_user_missing_password(self, client: AsyncClient) -> None:
        """Test registration fails when password is missing."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Test cases for login endpoint."""

    async def test_login_success_returns_jwt_token(self, client: AsyncClient) -> None:
        """Test successful login returns JWT token."""
        # First register a user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePassword123!",
            },
        )

        # Login with OAuth2PasswordRequestForm format
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "login@example.com",
                "password": "SecurePassword123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test login with invalid credentials returns 401."""
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "nonexistent@example.com",
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_wrong_password_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test login with wrong password returns 401."""
        # First register a user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "CorrectPassword123!",
            },
        )

        # Try to login with wrong password
        response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "wrongpass@example.com",
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401


class TestCurrentUser:
    """Test cases for /me endpoint (get current user)."""

    async def test_get_current_user_success(self, client: AsyncClient) -> None:
        """Test /me endpoint returns current user with valid token."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "me@example.com",
                "password": "SecurePassword123!",
            },
        )

        login_response = await client.post(
            "/api/v1/auth/token",
            data={
                "username": "me@example.com",
                "password": "SecurePassword123!",
            },
        )
        token = login_response.json()["access_token"]

        # Access protected /me endpoint
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_get_current_user_without_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test accessing /me without token returns 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_current_user_with_invalid_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test accessing /me with invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    async def test_get_current_user_with_expired_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        """Test accessing /me with expired token returns 401."""
        # Create an expired token manually
        from datetime import timedelta
        from app.auth import create_access_token

        # Create token that expired 1 hour ago
        expired_token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(hours=-1),
        )

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test cases for protected endpoint access patterns."""

    async def test_protected_endpoint_without_token(
        self, client: AsyncClient
    ) -> None:
        """Test that protected endpoints reject requests without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    async def test_protected_endpoint_with_malformed_header(
        self, client: AsyncClient
    ) -> None:
        """Test that malformed Authorization header is rejected."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "NotBearer token"},
        )
        assert response.status_code == 401
