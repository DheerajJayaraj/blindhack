from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Treatment, TreatmentOutcome
from app.schemas.outcomes import (
    TreatmentOutcomeCreate,
    TreatmentOutcomeResponse,
)

router = APIRouter(tags=["Treatment Outcomes"])


@router.post(
    "/api/treatments/{treatment_id}/outcomes",
    response_model=TreatmentOutcomeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_treatment_outcome(
    treatment_id: int,
    payload: TreatmentOutcomeCreate,
    db: Session = Depends(get_db),
):
    treatment = db.get(Treatment, treatment_id)
    if treatment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found.",
        )

    outcome_data = payload.model_dump(exclude={"recorded_at"})
    if payload.recorded_at is not None:
        outcome_data["recorded_at"] = payload.recorded_at

    outcome = TreatmentOutcome(
        treatment_id=treatment_id,
        **outcome_data,
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    return outcome


@router.get(
    "/api/treatments/{treatment_id}/outcomes",
    response_model=list[TreatmentOutcomeResponse],
)
def list_treatment_outcomes(
    treatment_id: int,
    db: Session = Depends(get_db),
):
    treatment = db.get(Treatment, treatment_id)
    if treatment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment not found.",
        )

    statement = (
        select(TreatmentOutcome)
        .where(TreatmentOutcome.treatment_id == treatment_id)
        .order_by(
            TreatmentOutcome.recorded_at,
            TreatmentOutcome.id,
        )
    )
    return db.scalars(statement).all()


@router.get(
    "/api/outcomes/{outcome_id}",
    response_model=TreatmentOutcomeResponse,
)
def get_treatment_outcome(
    outcome_id: int,
    db: Session = Depends(get_db),
):
    outcome = db.get(TreatmentOutcome, outcome_id)
    if outcome is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outcome not found.",
        )
    return outcome
