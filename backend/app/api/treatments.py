from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Condition, Treatment
from app.schemas.treatments import (
    TreatmentCreate,
    TreatmentResponse,
    TreatmentUpdate,
)

router = APIRouter(prefix="/api/treatments", tags=["Treatments"])


@router.post("", response_model=TreatmentResponse, status_code=status.HTTP_201_CREATED)
def create_treatment(
    payload: TreatmentCreate,
    db: Session = Depends(get_db),
):
    condition = db.get(Condition, payload.condition_id)
    if condition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condition not found.",
        )

    treatment = Treatment(**payload.model_dump())
    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    return treatment


@router.get("", response_model=list[TreatmentResponse])
def list_treatments(
    condition_id: int | None = None,
    db: Session = Depends(get_db),
):
    statement = select(Treatment).order_by(Treatment.id)

    if condition_id is not None:
        statement = statement.where(Treatment.condition_id == condition_id)

    return db.scalars(statement).all()


@router.get("/{treatment_id}", response_model=TreatmentResponse)
def get_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
):
    treatment = db.get(Treatment, treatment_id)
    if treatment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found.",
        )
    return treatment


@router.patch("/{treatment_id}", response_model=TreatmentResponse)
def update_treatment(
    treatment_id: int,
    payload: TreatmentUpdate,
    db: Session = Depends(get_db),
):
    treatment = db.get(Treatment, treatment_id)
    if treatment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found.",
        )

    updates = payload.model_dump(exclude_unset=True)

    if "name" in updates and (
        updates["name"] is None or not updates["name"].strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Treatment name cannot be empty.",
        )

    # Validate the final date range, including existing values not in the patch.
    start_date = updates.get("start_date", treatment.start_date)
    end_date = updates.get("end_date", treatment.end_date)

    if (
        start_date is not None
        and end_date is not None
        and end_date < start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date cannot precede start_date.",
        )

    for field, value in updates.items():
        setattr(treatment, field, value)

    db.commit()
    db.refresh(treatment)
    return treatment
