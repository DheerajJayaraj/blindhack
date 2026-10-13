from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConditionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    diagnosis_date: datetime | None = None
    status: str = Field(default="active", max_length=30)
    notes: str | None = None


class ConditionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    diagnosis_date: datetime | None = None
    status: str | None = Field(default=None, max_length=30)
    notes: str | None = None


class ConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    diagnosis_date: datetime | None
    status: str
    notes: str | None
    created_at: datetime
