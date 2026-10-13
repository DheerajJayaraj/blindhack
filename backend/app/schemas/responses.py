from pydantic import BaseModel


class AnalyzeResponse(BaseModel):
    """Standard response returned by the analysis endpoint."""

    task_id: int
    status: str
    result: str
