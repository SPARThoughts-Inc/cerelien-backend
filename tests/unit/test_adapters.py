"""Tests for infrastructure adapters."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.adapters.db.postgres import DatabaseAdapter
from app.infrastructure.adapters.firebase_auth_adapter import FirebaseAuthAdapter
from app.infrastructure.adapters.openai_realtime_adapter import OpenAIRealtimeAdapter
from app.infrastructure.adapters.twilio_adapter import TwilioAdapter


class TestDatabaseAdapter:
    def test_init(self):
        db = DatabaseAdapter()
        assert db._pool is None

    def test_ensure_pool_raises_when_not_connected(self):
        db = DatabaseAdapter()
        with pytest.raises(RuntimeError, match="not connected"):
            db._ensure_pool()

    @pytest.mark.asyncio
    async def test_connect_creates_pool(self):
        db = DatabaseAdapter()
        with patch("app.infrastructure.adapters.db.postgres.asyncpg") as mock_asyncpg:
            mock_pool = AsyncMock()
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)
            await db.connect()
            assert db._pool is not None

    @pytest.mark.asyncio
    async def test_connect_skips_if_already_connected(self):
        db = DatabaseAdapter()
        db._pool = MagicMock()
        with patch("app.infrastructure.adapters.db.postgres.asyncpg") as mock_asyncpg:
            mock_asyncpg.create_pool = AsyncMock()
            await db.connect()
            mock_asyncpg.create_pool.assert_not_called()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        db = DatabaseAdapter()
        mock_pool = AsyncMock()
        db._pool = mock_pool
        await db.disconnect()
        mock_pool.close.assert_called_once()
        assert db._pool is None

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self):
        db = DatabaseAdapter()
        await db.disconnect()  # Should not raise

    def test_ensure_pool_returns_pool(self):
        db = DatabaseAdapter()
        mock_pool = MagicMock()
        db._pool = mock_pool
        result = db._ensure_pool()
        assert result is mock_pool


class TestFirebaseAuthAdapter:
    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        adapter = FirebaseAuthAdapter()
        with patch.object(FirebaseAuthAdapter, "_ensure_initialized"), \
             patch("app.infrastructure.adapters.firebase_auth_adapter.auth") as mock_auth:
            mock_auth.verify_id_token.return_value = {
                "uid": "user123",
                "email": "test@example.com",
                "name": "Test User",
                "email_verified": True,
            }

            result = await adapter.verify_token("valid-token")

            assert result["uid"] == "user123"
            assert result["email"] == "test@example.com"
            assert result["email_verified"] is True

    @pytest.mark.asyncio
    async def test_verify_token_failure(self):
        from app.core.exceptions import AuthenticationError

        adapter = FirebaseAuthAdapter()
        with patch.object(FirebaseAuthAdapter, "_ensure_initialized"), \
             patch("app.infrastructure.adapters.firebase_auth_adapter.auth") as mock_auth:
            mock_auth.verify_id_token.side_effect = Exception("Token expired")

            with pytest.raises(AuthenticationError):
                await adapter.verify_token("bad-token")

    def test_ensure_initialized(self):
        FirebaseAuthAdapter._initialized = False
        with patch("app.infrastructure.adapters.firebase_auth_adapter.firebase_admin") as mock_fb:
            mock_fb._apps = {"default": True}
            FirebaseAuthAdapter._ensure_initialized()
            assert FirebaseAuthAdapter._initialized is True
        # Reset
        FirebaseAuthAdapter._initialized = False


class TestOpenAIRealtimeAdapter:
    def test_init(self):
        adapter = OpenAIRealtimeAdapter(system_instructions="Be helpful")
        assert adapter.system_instructions == "Be helpful"
        assert adapter.ws is None

    @pytest.mark.asyncio
    async def test_connect(self):
        adapter = OpenAIRealtimeAdapter(system_instructions="Test")
        mock_ws = AsyncMock()
        with patch("app.infrastructure.adapters.openai_realtime_adapter.websockets") as mock_websockets, \
             patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            mock_websockets.connect = AsyncMock(return_value=mock_ws)
            await adapter.connect()
            assert adapter.ws is mock_ws
            mock_ws.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_audio(self):
        adapter = OpenAIRealtimeAdapter()
        adapter.ws = AsyncMock()
        await adapter.send_audio("base64audiodata")
        adapter.ws.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_audio_no_ws(self):
        adapter = OpenAIRealtimeAdapter()
        await adapter.send_audio("data")  # Should not raise

    @pytest.mark.asyncio
    async def test_commit_audio(self):
        adapter = OpenAIRealtimeAdapter()
        adapter.ws = AsyncMock()
        await adapter.commit_audio()
        assert adapter.ws.send.call_count == 2

    @pytest.mark.asyncio
    async def test_commit_audio_no_ws(self):
        adapter = OpenAIRealtimeAdapter()
        await adapter.commit_audio()  # Should not raise

    @pytest.mark.asyncio
    async def test_close(self):
        adapter = OpenAIRealtimeAdapter()
        mock_ws = AsyncMock()
        adapter.ws = mock_ws
        await adapter.close()
        mock_ws.close.assert_called_once()
        assert adapter.ws is None

    @pytest.mark.asyncio
    async def test_close_no_ws(self):
        adapter = OpenAIRealtimeAdapter()
        await adapter.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_receive(self):
        adapter = OpenAIRealtimeAdapter()
        mock_ws = MagicMock()

        # Create a proper async iterator
        messages = [json.dumps({"type": "response.audio.delta", "delta": "abc"})]

        async def async_iter():
            for m in messages:
                yield m

        mock_ws.__aiter__ = lambda self: async_iter()
        adapter.ws = mock_ws

        events = []
        async for event in adapter.receive():
            events.append(event)

        assert len(events) == 1
        assert events[0]["type"] == "response.audio.delta"

    @pytest.mark.asyncio
    async def test_receive_no_ws(self):
        adapter = OpenAIRealtimeAdapter()
        events = []
        async for event in adapter.receive():
            events.append(event)
        assert events == []


class TestTwilioAdapter:
    def test_init(self):
        with patch.dict("os.environ", {
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_PHONE_NUMBER": "+15550001111",
        }):
            adapter = TwilioAdapter()
            assert adapter.account_sid == "AC123"
            assert adapter.phone_number == "+15550001111"

    def test_client_property_lazy_init(self):
        with patch.dict("os.environ", {
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_PHONE_NUMBER": "+15550001111",
        }):
            adapter = TwilioAdapter()
            assert adapter._client is None
            with patch("app.infrastructure.adapters.twilio_adapter.Client") as mock_client_cls:
                mock_client_cls.return_value = MagicMock()
                client = adapter.client
                assert client is not None
                # Second access should return same instance
                client2 = adapter.client
                assert client2 is client

    @pytest.mark.asyncio
    async def test_make_outbound_call(self):
        with patch.dict("os.environ", {
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_PHONE_NUMBER": "+15550001111",
        }):
            adapter = TwilioAdapter()
            mock_client = MagicMock()
            mock_call = MagicMock()
            mock_call.sid = "CA12345"
            mock_client.calls.create.return_value = mock_call
            adapter._client = mock_client

            result = await adapter.make_outbound_call("+15559876543", "wss://example.com/stream")
            assert result == "CA12345"

    def test_generate_voice_token(self):
        with patch.dict("os.environ", {
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_PHONE_NUMBER": "+15550001111",
            "TWILIO_TWIML_APP_SID": "AP123",
            "TWILIO_API_KEY": "SK123",
            "TWILIO_API_SECRET": "secret",
        }):
            adapter = TwilioAdapter()
            with patch("app.infrastructure.adapters.twilio_adapter.AccessToken") as mock_token_cls, \
                 patch("app.infrastructure.adapters.twilio_adapter.VoiceGrant"):
                mock_token = MagicMock()
                mock_token.to_jwt.return_value = "jwt-token-123"
                mock_token_cls.return_value = mock_token

                result = adapter.generate_voice_token("user1")
                assert result == "jwt-token-123"

    @pytest.mark.asyncio
    async def test_send_sms(self):
        with patch.dict("os.environ", {
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_PHONE_NUMBER": "+15550001111",
        }):
            adapter = TwilioAdapter()
            mock_client = MagicMock()
            mock_msg = MagicMock()
            mock_msg.sid = "SM12345"
            mock_client.messages.create.return_value = mock_msg
            adapter._client = mock_client

            result = await adapter.send_sms("+15559876543", "Hello!")
            assert result == "SM12345"
