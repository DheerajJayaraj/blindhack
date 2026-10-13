from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_empty_prompt_is_rejected():
    response = client.post(
        "/api/analyze",
        json={"prompt": ""},
    )

    assert response.status_code == 422


def test_missing_prompt_is_rejected():
    response = client.post(
        "/api/analyze",
        json={},
    )

    assert response.status_code == 422
