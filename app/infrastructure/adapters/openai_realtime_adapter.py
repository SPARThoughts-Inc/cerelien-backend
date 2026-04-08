import json
import logging
import os

import websockets

logger = logging.getLogger(__name__)

OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime-2025-08-28"


class OpenAIRealtimeAdapter:
    """Adapter for OpenAI Realtime API via WebSocket."""

    def __init__(self, system_instructions: str = ""):
        self.system_instructions = system_instructions
        self.ws = None

    async def connect(self):
        """Connect to the OpenAI Realtime WebSocket."""
        from app.core.config import settings
        api_key = settings.openai_api_key
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        self.ws = await websockets.connect(OPENAI_REALTIME_URL, additional_headers=headers)

        # Configure session
        session_config = {
            "type": "session.update",
            "session": {
                "turn_detection": {"type": "server_vad", "threshold": 0.7, "silence_duration_ms": 1000},
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "voice": "cedar",
                "instructions": self.system_instructions,
                "modalities": ["text", "audio"],
            },
        }
        await self.ws.send(json.dumps(session_config))
        logger.info("Connected to OpenAI Realtime API and configured session.")

    async def send_audio(self, audio_data: str):
        """Send base64-encoded audio data to OpenAI."""
        if self.ws:
            event = {
                "type": "input_audio_buffer.append",
                "audio": audio_data,
            }
            await self.ws.send(json.dumps(event))

    async def commit_audio(self):
        """Commit the audio buffer to trigger a response."""
        if self.ws:
            await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
            await self.ws.send(json.dumps({"type": "response.create"}))

    async def send_response_create(self):
        """Trigger the AI to generate a response proactively (e.g. greeting)."""
        if self.ws:
            await self.ws.send(json.dumps({"type": "response.create"}))

    async def receive(self):
        """Receive events from OpenAI. Yields parsed JSON events."""
        if self.ws:
            async for message in self.ws:
                event = json.loads(message)
                yield event

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.ws = None
            logger.info("Closed OpenAI Realtime connection.")
