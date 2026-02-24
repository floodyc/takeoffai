"""Job model — tracks processing jobs and results for the agentic pipeline."""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    upload_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Configuration
    label_pattern: Mapped[str] = mapped_column(String(100), default=r"LT\d{2,3}[A-Z]?")
    label_prefix: Mapped[str] = mapped_column(String(20), default="LT")
    pages: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of page indices
    detection_mode: Mapped[str] = mapped_column(String(20), default="thorough")  # fast | thorough
    model: Mapped[str] = mapped_column(String(100), default="claude-haiku-4-5-20251001")

    # Crop bounds (stored as JSON)
    crop_bounds: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    progress_message: Mapped[str] = mapped_column(String(500), default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metrics
    vlm_calls_used: Mapped[int] = mapped_column(Integer, default=0)
    phase_log: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Output
    output_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sheets: Mapped[list["SheetResult"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class SheetResult(Base):
    __tablename__ = "sheet_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
    page_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_label: Mapped[str] = mapped_column(String(255), default="")

    # Results
    final_counts: Mapped[dict] = mapped_column(JSON, default=dict)
    total: Mapped[int] = mapped_column(Integer, default=0)
    detections: Mapped[list | None] = mapped_column(JSON, nullable=True)  # per-fixture detail
    duplicates_removed: Mapped[int] = mapped_column(Integer, default=0)
    pattern_warnings: Mapped[list] = mapped_column(JSON, default=list)

    # Context + agent data
    drawing_context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    agent_log: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    vlm_calls_used: Mapped[int] = mapped_column(Integer, default=0)
    elapsed_s: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationship
    job: Mapped["Job"] = relationship(back_populates="sheets")
