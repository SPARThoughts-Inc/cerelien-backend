from fastapi import Depends, Request

from app.core.exceptions import AuthenticationError
from app.infrastructure.adapters.firebase_auth_adapter import FirebaseAuthAdapter

_firebase_adapter = FirebaseAuthAdapter()


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency that extracts and verifies the Firebase Bearer token.

    Returns the decoded user claims dict with uid, email, etc.
    Raises AuthenticationError (401) if the token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    token = auth_header.split("Bearer ", 1)[1]
    return await _firebase_adapter.verify_token(token)
