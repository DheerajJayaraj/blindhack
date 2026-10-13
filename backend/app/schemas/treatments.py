from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


TreatmentType = Literal[
    "medication",
    "procedure",
    "lifestyle",
    "ayurveda",
    "therapy",
    "other",
]

TreatmentStatus = Literal[
    "planned",
    "active",
    "completed",
    "discontinued",
]


class TreatmentCreate(BaseModel):
    condition_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    treatment_type: TreatmentType
    provider_name: str | None = Field(default=None, max_length=200)
    start_date: datetime | None = None
    end_date: datetime | None = None
    prescribed_regimen: str | None = None
    status: TreatmentStatus = "active"
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot precede start_date.")
        return self


class TreatmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    treatment_type: TreatmentType | None = None
    provider_name: str | None = Field(default=None, max_length=200)
    start_date: datetime | None = None
    end_date: datetime | None = None
    prescribed_regimen: str | None = None
    status: TreatmentStatus | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date cannot precede start_date.")
        return self


class TreatmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    condition_id: int
    name: str
    treatment_type: str
    provider_name: str | None
    start_date: datetime | None
    end_date: datetime | None
    prescribed_regimen: str | None
    status: str
    notes: str | None
    created_at: datetime
