import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import TaskRecord
from app.schemas.requests import AnalyzeRequest
from app.schemas.responses import AnalyzeResponse
from app.services.external_api import analyze_with_gemini


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def home():
    return {
        "message": "Hackathon Backend is running!",
        "status": "online",
    }


@router.get("/api/health")
def health():
    return {"status": "online"}


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    record = TaskRecord(
        task_type="gemini_analysis",
        status="processing",
        input_data={"prompt": request.prompt},
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    task_id = record.id
    logger.info("Analysis started: task_id=%s", task_id)

    try:
        api_response = await analyze_with_gemini(request.prompt)

        candidates = api_response.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini returned no response candidates.")

        parts = candidates[0].get("content", {}).get("parts", [])
        result_text = "\n".join(
            part["text"]
            for part in parts
            if isinstance(part.get("text"), str)
        )

        if not result_text:
            raise ValueError("Gemini returned no text response.")

        record.status = "completed"
        record.result = {"text": result_text}
        record.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(record)

        logger.info("Analysis completed: task_id=%s", task_id)

        return AnalyzeResponse(
            task_id=record.id,
            status=record.status,
            result=result_text,
        )

    except Exception as exc:
        logger.exception(
            "Analysis failed: task_id=%s error_type=%s",
            task_id,
            type(exc).__name__,
        )

        db.rollback()

        try:
            record = db.get(TaskRecord, task_id)

            if record is not None:
                record.status = "failed"
                record.error_message = type(exc).__name__
                record.completed_at = datetime.now(timezone.utc)
                db.commit()

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to save task failure status: task_id=%s",
                task_id,
            )

        raise HTTPException(
            status_code=502,
            detail="Analysis failed. Check backend logs for details.",
        ) from exc
