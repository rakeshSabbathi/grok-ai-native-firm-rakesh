"""Thin Grok (xAI) client. xAI's API is OpenAI-compatible, so we use the openai SDK."""
import os


def model() -> str:
    return os.environ.get("GROK_MODEL", "grok-4")


def client():
    from openai import OpenAI  # lazy import so tests run without the SDK

    key = os.environ.get("XAI_API_KEY")
    if not key:
        raise SystemExit("XAI_API_KEY is not set. Copy .env.example to .env and add your key.")
    return OpenAI(api_key=key, base_url=os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1"))
