from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.conditions import router as conditions_router
from app.api.treatments import router as treatments_router
from app.api.outcomes import router as outcomes_router
from app.api.measurements import router as measurements_router
from app.api.routes import router
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.db.database import create_tables


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables before serving requests."""
    create_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Medical Twin API",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(conditions_router)
app.include_router(treatments_router)
app.include_router(outcomes_router)
app.include_router(measurements_router)
