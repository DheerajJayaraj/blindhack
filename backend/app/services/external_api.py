import asyncio

import httpx

from app.core.config import settings


GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.8-flash:generateContent"
)

MAX_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


async def analyze_with_gemini(prompt: str) -> dict:
    """Call Gemini and retry transient failures with exponential backoff."""
    if not settings.external_api_key:
        raise RuntimeError("Gemini API key is not configured.")

    headers = {
        "x-goog-api-key": settings.external_api_key,
        "Content-Type": "application/json",
    }
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = await client.post(
                    GEMINI_API_URL,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                if attempt == MAX_ATTEMPTS:
                    raise

            except httpx.HTTPStatusError as exc:
                if (
                    exc.response.status_code not in RETRYABLE_STATUS_CODES
                    or attempt == MAX_ATTEMPTS
                ):
                    raise

            delay = 2 ** (attempt - 1)
            await asyncio.sleep(delay)

    raise RuntimeError("Gemini request attempts exhausted.")
