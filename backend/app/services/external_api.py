import httpx

from app.core.config import settings


GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-3.8-flash:generateContent"
)


async def analyze_with_gemini(prompt: str) -> dict:
    """Send a prompt to Gemini and return its JSON response."""

    if not settings.external_api_key:
        raise RuntimeError("Gemini API key is not configured.")

    headers = {
        "x-goog-api-key": settings.external_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            GEMINI_API_URL,
            headers=headers,
            json=payload,
        )

        response.raise_for_status()

        return response.json()
