from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Validate an incoming analysis request."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The prompt to send for analysis.",
    )
