from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MeasurementSource = Literal[
    "patient_reported",
    "clinician_reported",
    "lab_result",
    "device_recorded",
    "other",
]


class MeasurementCreate(BaseModel):
    condition_id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1, max_length=150)
    value: float
    unit: str = Field(min_length=1, max_length=50)
    measured_at: datetime
    source: MeasurementSource = "patient_reported"
    notes: str | None = None


class MeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    condition_id: int | None
    name: str
    value: float
    unit: str
    measured_at: datetime
    source: str
    notes: str | None
    created_at: datetime
