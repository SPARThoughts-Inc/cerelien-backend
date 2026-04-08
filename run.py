"""Start the backend with .env loaded before anything else.

CRITICAL: The OpenAI Agents SDK resolves API keys at import time.
We must set os.environ['OPENAI_API_KEY'] and call set_default_openai_key()
BEFORE importing any app modules or agents.

We import the app object directly (not as a string) so uvicorn does NOT
spawn a subprocess that would lose our env/globals.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 1. Load .env FIRST — before any other imports
load_dotenv(Path(__file__).parent / ".env", override=True)

api_key = os.environ.get("OPENAI_API_KEY", "")
print(f"[run.py] OPENAI_API_KEY set: {bool(api_key)}, len={len(api_key)}", flush=True)

# 2. Set the default key in the agents SDK BEFORE importing app modules
from agents import set_default_openai_key, set_tracing_disabled  # noqa: E402

set_default_openai_key(api_key)
set_tracing_disabled(True)
print("[run.py] set_default_openai_key() called successfully", flush=True)

# 3. Import the app directly so uvicorn stays in-process (no subprocess = globals preserved)
from app.main import app  # noqa: E402
import uvicorn  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
