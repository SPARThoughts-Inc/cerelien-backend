import logging
import os

from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.rest import Client

logger = logging.getLogger(__name__)


class TwilioAdapter:
    """Adapter for Twilio voice and SMS services."""

    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        self.phone_number = os.environ.get("TWILIO_PHONE_NUMBER", "")
        self._client = None

    @property
    def client(self) -> Client:
        if self._client is None:
            self._client = Client(self.account_sid, self.auth_token)
        return self._client

    async def make_outbound_call(self, to: str, stream_url: str) -> str:
        """Make an outbound call with media streaming. Returns the call SID."""
        twiml = (
            f'<Response>'
            f'<Say>Please hold while we connect you to your diabetes consultant.</Say>'
            f'<Connect><Stream url="{stream_url}" /></Connect>'
            f'</Response>'
        )
        call = self.client.calls.create(
            to=to,
            from_=self.phone_number,
            twiml=twiml,
        )
        logger.info("Outbound call created: %s", call.sid)
        return call.sid

    def generate_voice_token(self, identity: str) -> str:
        """Generate a Twilio access token for client-side voice."""
        twiml_app_sid = os.environ.get("TWILIO_TWIML_APP_SID", "")
        api_key = os.environ.get("TWILIO_API_KEY", "")
        api_secret = os.environ.get("TWILIO_API_SECRET", "")

        token = AccessToken(
            self.account_sid,
            api_key,
            api_secret,
            identity=identity,
        )
        voice_grant = VoiceGrant(
            outgoing_application_sid=twiml_app_sid,
            incoming_allow=True,
        )
        token.add_grant(voice_grant)
        return token.to_jwt()

    async def send_sms(self, to: str, body: str) -> str:
        """Send an SMS message. Returns the message SID."""
        message = self.client.messages.create(
            to=to,
            from_=self.phone_number,
            body=body,
        )
        logger.info("SMS sent: %s", message.sid)
        return message.sid
