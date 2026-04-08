import logging

import firebase_admin
from firebase_admin import auth, credentials

from app.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class FirebaseAuthAdapter:
    """Adapter for Firebase Authentication token verification."""

    _initialized = False

    @classmethod
    def _ensure_initialized(cls):
        """Lazily initialize the Firebase app."""
        if not cls._initialized:
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
            cls._initialized = True

    async def verify_token(self, id_token: str) -> dict:
        """Verify a Firebase ID token and return the decoded claims.

        Returns a dict with uid, email, and other claims.
        Raises AuthenticationError if the token is invalid.
        """
        self._ensure_initialized()
        try:
            decoded = auth.verify_id_token(id_token)
            return {
                "uid": decoded["uid"],
                "email": decoded.get("email"),
                "name": decoded.get("name"),
                "email_verified": decoded.get("email_verified", False),
            }
        except Exception as e:
            logger.warning("Firebase token verification failed: %s", str(e))
            raise AuthenticationError("Invalid or expired authentication token")
