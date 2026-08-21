from functools import lru_cache

from google import genai

from app.core.config import get_settings


# Only place a Gemini client gets created — don't call genai.Client() elsewhere.
@lru_cache
def get_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)
