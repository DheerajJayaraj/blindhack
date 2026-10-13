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


def create_test_condition(client, name="Synthetic test condition"):
    response = client.post(
        "/api/conditions",
        json={"name": name, "notes": "Synthetic test record"},
    )
    assert response.status_code == 201
    return response.json()


def create_test_treatment(client, condition_id, name="Test medication"):
    return client.post(
        "/api/treatments",
        json={
            "condition_id": condition_id,
            "name": name,
            "treatment_type": "medication",
            "status": "active",
            "prescribed_regimen": "Synthetic test regimen",
        },
    )


def test_create_treatment(client):
    condition = create_test_condition(client)

    response = create_test_treatment(client, condition["id"])

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Test medication"
    assert body["condition_id"] == condition["id"]
    assert body["treatment_type"] == "medication"
    assert body["status"] == "active"
    assert body["id"] > 0


def test_create_treatment_for_missing_condition_returns_404(client):
    response = create_test_treatment(client, 99999)

    assert response.status_code == 404


def test_list_and_filter_treatments(client):
    first_condition = create_test_condition(client, "Condition A")
    second_condition = create_test_condition(client, "Condition B")

    first = create_test_treatment(
        client, first_condition["id"], "Treatment A"
    )
    second = create_test_treatment(
        client, second_condition["id"], "Treatment B"
    )
    assert first.status_code == 201
    assert second.status_code == 201

    all_response = client.get("/api/treatments")
    filtered_response = client.get(
        f"/api/treatments?condition_id={first_condition['id']}"
    )

    assert all_response.status_code == 200
    assert len(all_response.json()) == 2
    assert filtered_response.status_code == 200
    assert len(filtered_response.json()) == 1
    assert filtered_response.json()[0]["name"] == "Treatment A"


def test_get_treatment(client):
    condition = create_test_condition(client)
    created = create_test_treatment(client, condition["id"]).json()

    response = client.get(f"/api/treatments/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_missing_treatment_returns_404(client):
    response = client.get("/api/treatments/99999")

    assert response.status_code == 404


def test_update_treatment(client):
    condition = create_test_condition(client)
    created = create_test_treatment(client, condition["id"]).json()

    response = client.patch(
        f"/api/treatments/{created['id']}",
        json={
            "status": "completed",
            "notes": "Synthetic outcome follow-up",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["notes"] == "Synthetic outcome follow-up"


def test_invalid_treatment_type_is_rejected(client):
    condition = create_test_condition(client)

    response = client.post(
        "/api/treatments",
        json={
            "condition_id": condition["id"],
            "name": "Invalid test treatment",
            "treatment_type": "not_a_valid_type",
        },
    )

    assert response.status_code == 422


def test_invalid_date_range_is_rejected(client):
    condition = create_test_condition(client)

    response = client.post(
        "/api/treatments",
        json={
            "condition_id": condition["id"],
            "name": "Date validation test",
            "treatment_type": "medication",
            "start_date": "2026-10-10T00:00:00",
            "end_date": "2026-10-01T00:00:00",
        },
    )

    assert response.status_code == 422
