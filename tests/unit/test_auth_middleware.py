"""Tests for Firebase auth middleware."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import AuthenticationError
from app.main import create_app


@pytest.fixture
def app():
    """Create a test app with a protected endpoint."""
    from fastapi import Depends

    application = create_app()

    # Add a test-only protected route
    from app.api.middleware.auth import get_current_user

    @application.get("/api/test-protected")
    async def protected_route(user: dict = Depends(get_current_user)):
        return {"uid": user["uid"], "email": user["email"]}

    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestAuthMiddleware:
    @pytest.mark.asyncio
    async def test_missing_header_returns_401(self, client):
        response = await client.get("/api/test-protected")
        assert response.status_code == 401
        assert "Missing or invalid Authorization header" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_header_format_returns_401(self, client):
        response = await client.get(
            "/api/test-protected",
            headers={"Authorization": "Token abc123"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    @patch("app.api.middleware.auth._firebase_adapter")
    async def test_valid_token_returns_user(self, mock_adapter, client):
        mock_adapter.verify_token = AsyncMock(
            return_value={
                "uid": "firebase-uid-123",
                "email": "patient@example.com",
                "name": "John Doe",
                "email_verified": True,
            }
        )

        response = await client.get(
            "/api/test-protected",
            headers={"Authorization": "Bearer valid-token-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["uid"] == "firebase-uid-123"
        assert data["email"] == "patient@example.com"

    @pytest.mark.asyncio
    @patch("app.api.middleware.auth._firebase_adapter")
    async def test_invalid_token_returns_401(self, mock_adapter, client):
        mock_adapter.verify_token = AsyncMock(
            side_effect=AuthenticationError("Invalid or expired authentication token")
        )

        response = await client.get(
            "/api/test-protected",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401
