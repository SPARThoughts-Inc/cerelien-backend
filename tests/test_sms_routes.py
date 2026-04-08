"""Tests for SMS routes."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_sms_workflow
from app.domain.workflows.sms_workflow import SMSWorkflow
from app.main import create_app


@pytest.fixture
def mock_workflow():
    return AsyncMock(spec=SMSWorkflow)


@pytest.fixture
def app(mock_workflow):
    application = create_app()
    application.dependency_overrides[get_sms_workflow] = lambda: mock_workflow
    return application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestIncomingSMS:
    @pytest.mark.asyncio
    async def test_incoming_sms_returns_twiml(self, client, mock_workflow):
        mock_workflow.handle_incoming_sms.return_value = "Your glucose looks good today!"

        response = await client.post(
            "/api/sms/incoming",
            data={"From": "+15551234567", "Body": "How is my glucose?"},
        )

        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]
        assert "<Response>" in response.text
        assert "<Message>" in response.text
        assert "Your glucose looks good today!" in response.text
        mock_workflow.handle_incoming_sms.assert_called_once_with(
            from_number="+15551234567", body="How is my glucose?"
        )
