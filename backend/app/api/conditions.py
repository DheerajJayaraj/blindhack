from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Condition
from app.schemas.conditions import (
    ConditionCreate,
    ConditionResponse,
    ConditionUpdate,
)


router = APIRouter(prefix="/api/conditions", tags=["Medical Conditions"])

ConditionStatus = Literal["active", "resolved", "inactive"]


@router.post(
    "",
    response_model=ConditionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_condition(
    payload: ConditionCreate,
    db: Session = Depends(get_db),
):
    condition = Condition(**payload.model_dump())
    db.add(condition)
    db.commit()
    db.refresh(condition)
    return condition


@router.get("", response_model=list[ConditionResponse])
def list_conditions(db: Session = Depends(get_db)):
    statement = select(Condition).order_by(Condition.id)
    return db.scalars(statement).all()


@router.get("/{condition_id}", response_model=ConditionResponse)
def get_condition(
    condition_id: int,
    db: Session = Depends(get_db),
):
    condition = db.get(Condition, condition_id)
    if condition is None:
        raise HTTPException(status_code=404, detail="Condition not found.")
    return condition


@router.patch("/{condition_id}", response_model=ConditionResponse)
def update_condition(
    condition_id: int,
    payload: ConditionUpdate,
    db: Session = Depends(get_db),
):
    condition = db.get(Condition, condition_id)
    if condition is None:
        raise HTTPException(status_code=404, detail="Condition not found.")

    updates = payload.model_dump(exclude_unset=True)

    if "name" in updates and updates["name"] is None:
        raise HTTPException(status_code=422, detail="Name cannot be null.")

    if "status" in updates and updates["status"] not in {
        "active", "resolved", "inactive"
    }:
        raise HTTPException(
            status_code=422,
            detail="Status must be active, resolved, or inactive.",
        )

    for field, value in updates.items():
        setattr(condition, field, value)

    db.commit()
    db.refresh(condition)
    return condition
