"""Cerelien Backend - ensure OpenAI key is set at package import time."""
import os

from agents import set_default_openai_key, set_tracing_disabled

# Re-apply the default key in case this module is imported in a context
# where run.py hasn't already done it (e.g., tests, direct uvicorn CLI).
_key = os.environ.get("OPENAI_API_KEY", "")
if _key:
    set_default_openai_key(_key)
    set_tracing_disabled(True)
