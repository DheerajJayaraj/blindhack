import httpx
import pytest

from app.services import external_api


class FakeResponse:
    def __init__(self, status_code: int, data: dict | None = None):
        self.status_code = status_code
        self._data = data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", external_api.GEMINI_API_URL)
            response = httpx.Response(
                self.status_code,
                request=request,
            )
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=request,
                response=response,
            )

    def json(self):
        return self._data


class FakeAsyncClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, *args, **kwargs):
        self.calls += 1
        return next(self.responses)


@pytest.mark.anyio
async def test_gemini_retries_transient_failure_then_succeeds(monkeypatch):
    fake_client = FakeAsyncClient(
        [
            FakeResponse(503),
            FakeResponse(
                200,
                {"candidates": [{"content": {"parts": [{"text": "Success"}]}}]},
            ),
        ]
    )
    delays = []

    monkeypatch.setattr(
        external_api.httpx,
        "AsyncClient",
        lambda **kwargs: fake_client,
    )

    async def fake_sleep(seconds):
        delays.append(seconds)

    monkeypatch.setattr(external_api.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(external_api.settings, "external_api_key", "test-key")

    result = await external_api.analyze_with_gemini("Test prompt")

    assert result["candidates"][0]["content"]["parts"][0]["text"] == "Success"
    assert fake_client.calls == 2
    assert delays == [1]


@pytest.mark.anyio
async def test_gemini_stops_after_max_attempts(monkeypatch):
    fake_client = FakeAsyncClient(
        [FakeResponse(503) for _ in range(external_api.MAX_ATTEMPTS)]
    )
    delays = []

    monkeypatch.setattr(
        external_api.httpx,
        "AsyncClient",
        lambda **kwargs: fake_client,
    )

    async def fake_sleep(seconds):
        delays.append(seconds)

    monkeypatch.setattr(external_api.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(external_api.settings, "external_api_key", "test-key")

    with pytest.raises(httpx.HTTPStatusError):
        await external_api.analyze_with_gemini("Test prompt")

    assert fake_client.calls == external_api.MAX_ATTEMPTS
    assert delays == [1, 2]
