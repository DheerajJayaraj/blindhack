from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


OutcomeType = Literal[
    "improved",
    "unchanged",
    "worsened",
    "side_effect",
    "adherence",
    "other",
]

OutcomeSource = Literal[
    "patient_reported",
    "clinician_reported",
    "lab_result",
    "device_recorded",
    "other",
]


class TreatmentOutcomeCreate(BaseModel):
    recorded_at: datetime | None = None
    outcome_type: OutcomeType
    description: str = Field(min_length=1, max_length=5000)
    source: OutcomeSource = "patient_reported"


class TreatmentOutcomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    treatment_id: int
    recorded_at: datetime
    outcome_type: str
    description: str
    source: str
    created_at: datetime
