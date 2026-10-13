from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Condition, HealthMeasurement
from app.schemas.measurements import (
    MeasurementCreate,
    MeasurementResponse,
)

router = APIRouter(tags=["Health Measurements"])


@router.post(
    "/api/measurements",
    response_model=MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_measurement(
    payload: MeasurementCreate,
    db: Session = Depends(get_db),
):
    if payload.condition_id is not None:
        condition = db.get(Condition, payload.condition_id)
        if condition is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Condition not found.",
            )

    measurement = HealthMeasurement(**payload.model_dump())
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.get(
    "/api/measurements",
    response_model=list[MeasurementResponse],
)
def list_measurements(
    condition_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    statement = select(HealthMeasurement)

    if condition_id is not None:
        statement = statement.where(
            HealthMeasurement.condition_id == condition_id
        )

    statement = statement.order_by(
        HealthMeasurement.measured_at,
        HealthMeasurement.id,
    )
    return db.scalars(statement).all()


@router.get(
    "/api/measurements/{measurement_id}",
    response_model=MeasurementResponse,
)
def get_measurement(
    measurement_id: int,
    db: Session = Depends(get_db),
):
    measurement = db.get(HealthMeasurement, measurement_id)
    if measurement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Measurement not found.",
        )
    return measurement
