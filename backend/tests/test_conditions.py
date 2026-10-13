import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_create_condition(client):
    response = client.post(
        "/api/conditions",
        json={
            "name": "Type 2 diabetes",
            "status": "active",
            "notes": "Synthetic test record",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Type 2 diabetes"
    assert body["status"] == "active"
    assert body["id"] > 0


def test_list_conditions(client):
    client.post(
        "/api/conditions",
        json={"name": "Condition A"},
    )
    client.post(
        "/api/conditions",
        json={"name": "Condition B"},
    )

    response = client.get("/api/conditions")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_condition(client):
    created = client.post(
        "/api/conditions",
        json={"name": "Asthma"},
    ).json()

    response = client.get(f"/api/conditions/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Asthma"


def test_update_condition(client):
    created = client.post(
        "/api/conditions",
        json={"name": "Hypertension"},
    ).json()

    response = client.patch(
        f"/api/conditions/{created['id']}",
        json={"status": "resolved", "notes": "Updated test note"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "resolved"
    assert response.json()["notes"] == "Updated test note"


def test_missing_condition_returns_404(client):
    response = client.get("/api/conditions/99999")

    assert response.status_code == 404


def test_invalid_status_is_rejected(client):
    created = client.post(
        "/api/conditions",
        json={"name": "Test condition"},
    ).json()

    response = client.patch(
        f"/api/conditions/{created['id']}",
        json={"status": "unknown"},
    )

    assert response.status_code == 422


def test_empty_condition_name_is_rejected(client):
    response = client.post(
        "/api/conditions",
        json={"name": ""},
    )

    assert response.status_code == 422
