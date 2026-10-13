from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskRecord(Base):
    __tablename__ = "task_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False
    )
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Condition(Base):
    __tablename__ = "conditions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    diagnosis_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default="active", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    treatments: Mapped[list["Treatment"]] = relationship(
        back_populates="condition",
        cascade="all, delete-orphan",
    )
    measurements: Mapped[list["HealthMeasurement"]] = relationship(
        back_populates="condition",
        cascade="all, delete-orphan",
    )


class Treatment(Base):
    __tablename__ = "treatments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    condition_id: Mapped[int] = mapped_column(
        ForeignKey("conditions.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    treatment_type: Mapped[str] = mapped_column(
        String(80), nullable=False
    )
    provider_name: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    prescribed_regimen: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default="active", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    condition: Mapped["Condition"] = relationship(
        back_populates="treatments"
    )
    outcomes: Mapped[list["TreatmentOutcome"]] = relationship(
        back_populates="treatment",
        cascade="all, delete-orphan",
    )


class HealthMeasurement(Base):
    __tablename__ = "health_measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    condition_id: Mapped[int | None] = mapped_column(
        ForeignKey("conditions.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(
        String(100), default="patient_reported", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    condition: Mapped["Condition | None"] = relationship(
        back_populates="measurements"
    )


class TreatmentOutcome(Base):
    __tablename__ = "treatment_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    treatment_id: Mapped[int] = mapped_column(
        ForeignKey("treatments.id"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    outcome_type: Mapped[str] = mapped_column(
        String(80), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(
        String(100), default="patient_reported", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    treatment: Mapped["Treatment"] = relationship(
        back_populates="outcomes"
    )
