from datetime import datetime

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


def create_test_measurement(
    client,
    name="Synthetic test measurement",
    condition_id=None,
    value=72.5,
    unit="bpm",
    measured_at="2026-10-12T10:00:00",
):
    payload = {
        "name": name,
        "value": value,
        "unit": unit,
        "measured_at": measured_at,
        "notes": "Synthetic test observation",
    }
    if condition_id is not None:
        payload["condition_id"] = condition_id

    return client.post("/api/measurements", json=payload)


def test_create_measurement(client):
    condition = create_test_condition(client)

    response = create_test_measurement(
        client,
        condition_id=condition["id"],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["condition_id"] == condition["id"]
    assert body["name"] == "Synthetic test measurement"
    assert body["value"] == 72.5
    assert body["unit"] == "bpm"
    assert body["source"] == "patient_reported"
    assert body["id"] > 0


def test_create_measurement_without_condition(client):
    response = create_test_measurement(client)

    assert response.status_code == 201
    assert response.json()["condition_id"] is None


def test_measurement_for_missing_condition_returns_404(client):
    response = create_test_measurement(client, condition_id=99999)

    assert response.status_code == 404


def test_list_measurements_in_chronological_order(client):
    later = create_test_measurement(
        client,
        name="Later synthetic observation",
        measured_at="2026-10-12T10:00:00",
    )
    earlier = create_test_measurement(
        client,
        name="Earlier synthetic observation",
        measured_at="2026-10-10T10:00:00",
    )

    assert later.status_code == 201
    assert earlier.status_code == 201

    response = client.get("/api/measurements")

    assert response.status_code == 200
    measurements = response.json()
    assert len(measurements) == 2
    assert measurements[0]["name"] == "Earlier synthetic observation"
    assert measurements[1]["name"] == "Later synthetic observation"


def test_filter_measurements_by_condition(client):
    first_condition = create_test_condition(client, "Synthetic condition A")
    second_condition = create_test_condition(client, "Synthetic condition B")

    first = create_test_measurement(
        client,
        name="Measurement A",
        condition_id=first_condition["id"],
    )
    second = create_test_measurement(
        client,
        name="Measurement B",
        condition_id=second_condition["id"],
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        "/api/measurements",
        params={"condition_id": first_condition["id"]},
    )

    assert response.status_code == 200
    measurements = response.json()
    assert len(measurements) == 1
    assert measurements[0]["name"] == "Measurement A"
    assert measurements[0]["condition_id"] == first_condition["id"]


def test_get_measurement(client):
    created = create_test_measurement(client)
    assert created.status_code == 201

    measurement_id = created.json()["id"]
    response = client.get(f"/api/measurements/{measurement_id}")

    assert response.status_code == 200
    assert response.json()["id"] == measurement_id


def test_missing_measurement_returns_404(client):
    response = client.get("/api/measurements/99999")

    assert response.status_code == 404


def test_invalid_measurement_source_is_rejected(client):
    response = client.post(
        "/api/measurements",
        json={
            "name": "Synthetic observation",
            "value": 10,
            "unit": "units",
            "measured_at": "2026-10-12T10:00:00",
            "source": "invalid_source",
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"unit": ""},
    ],
)
def test_empty_required_text_fields_are_rejected(client, overrides):
    payload = {
        "name": "Synthetic observation",
        "value": 10,
        "unit": "units",
        "measured_at": "2026-10-12T10:00:00",
    }
    payload.update(overrides)

    response = client.post("/api/measurements", json=payload)

    assert response.status_code == 422
