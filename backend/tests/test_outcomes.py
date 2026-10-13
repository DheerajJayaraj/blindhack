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


def create_test_treatment(client):
    condition_response = client.post(
        "/api/conditions",
        json={"name": "Synthetic test condition"},
    )
    assert condition_response.status_code == 201
    condition_id = condition_response.json()["id"]

    treatment_response = client.post(
        "/api/treatments",
        json={
            "condition_id": condition_id,
            "name": "Synthetic test treatment",
            "treatment_type": "medication",
            "status": "active",
        },
    )
    assert treatment_response.status_code == 201
    return treatment_response.json()


def test_create_outcome(client):
    treatment = create_test_treatment(client)

    response = client.post(
        f"/api/treatments/{treatment['id']}/outcomes",
        json={
            "outcome_type": "improved",
            "description": "Synthetic observation: reported improvement.",
            "source": "patient_reported",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["treatment_id"] == treatment["id"]
    assert body["outcome_type"] == "improved"
    assert body["source"] == "patient_reported"
    assert body["id"] > 0


def test_outcome_defaults_to_patient_reported(client):
    treatment = create_test_treatment(client)

    response = client.post(
        f"/api/treatments/{treatment['id']}/outcomes",
        json={
            "outcome_type": "unchanged",
            "description": "Synthetic observation.",
        },
    )

    assert response.status_code == 201
    assert response.json()["source"] == "patient_reported"


def test_missing_treatment_returns_404(client):
    response = client.post(
        "/api/treatments/99999/outcomes",
        json={
            "outcome_type": "other",
            "description": "Synthetic observation.",
        },
    )

    assert response.status_code == 404


def test_list_outcomes_in_chronological_order(client):
    treatment = create_test_treatment(client)
    endpoint = f"/api/treatments/{treatment['id']}/outcomes"

    later = client.post(
        endpoint,
        json={
            "recorded_at": "2026-10-12T10:00:00",
            "outcome_type": "unchanged",
            "description": "Later synthetic observation.",
        },
    )
    earlier = client.post(
        endpoint,
        json={
            "recorded_at": "2026-10-10T10:00:00",
            "outcome_type": "improved",
            "description": "Earlier synthetic observation.",
        },
    )

    assert later.status_code == 201
    assert earlier.status_code == 201

    response = client.get(endpoint)

    assert response.status_code == 200
    outcomes = response.json()
    assert len(outcomes) == 2
    assert outcomes[0]["description"] == "Earlier synthetic observation."
    assert outcomes[1]["description"] == "Later synthetic observation."


def test_get_outcome(client):
    treatment = create_test_treatment(client)
    created = client.post(
        f"/api/treatments/{treatment['id']}/outcomes",
        json={
            "outcome_type": "side_effect",
            "description": "Synthetic reported side effect.",
        },
    ).json()

    response = client.get(f"/api/outcomes/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_missing_outcome_returns_404(client):
    response = client.get("/api/outcomes/99999")

    assert response.status_code == 404


def test_invalid_outcome_type_is_rejected(client):
    treatment = create_test_treatment(client)

    response = client.post(
        f"/api/treatments/{treatment['id']}/outcomes",
        json={
            "outcome_type": "not_valid",
            "description": "Synthetic observation.",
        },
    )

    assert response.status_code == 422


def test_empty_description_is_rejected(client):
    treatment = create_test_treatment(client)

    response = client.post(
        f"/api/treatments/{treatment['id']}/outcomes",
        json={
            "outcome_type": "other",
            "description": "",
        },
    )

    assert response.status_code == 422
