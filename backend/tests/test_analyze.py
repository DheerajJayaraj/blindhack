from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import router
from app.db.database import Base, get_db
from app.db.models import TaskRecord
from app.main import app


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_analyze_success(monkeypatch):
    async def fake_gemini(prompt: str) -> dict:
        assert prompt == "Explain phishing"
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Phishing is a deceptive cyberattack."}
                        ]
                    }
                }
            ]
        }

    monkeypatch.setattr(
        "app.api.routes.analyze_with_gemini",
        fake_gemini,
    )

    response = client.post(
        "/api/analyze",
        json={"prompt": "Explain phishing"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["task_id"] > 0
    assert body["status"] == "completed"
    assert body["result"] == "Phishing is a deceptive cyberattack."


def test_analyze_gemini_failure(monkeypatch):
    async def fake_gemini(prompt: str) -> dict:
        raise RuntimeError("Simulated external API failure")

    monkeypatch.setattr(
        "app.api.routes.analyze_with_gemini",
        fake_gemini,
    )

    response = client.post(
        "/api/analyze",
        json={"prompt": "Test a failure"},
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Analysis failed. Check backend logs for details."
    }

    db = TestSessionLocal()
    try:
        record = (
            db.query(TaskRecord)
            .filter(TaskRecord.input_data["prompt"].as_string() == "Test a failure")
            .first()
        )

        assert record is not None
        assert record.status == "failed"
        assert record.error_message == "RuntimeError"
        assert record.completed_at is not None
    finally:
        db.close()


def teardown_module():
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
