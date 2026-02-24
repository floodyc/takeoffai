"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from pydantic import BaseModel, EmailStr


# --- Auth ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    created_at: datetime


# --- Jobs ---

class CropBoundsSchema(BaseModel):
    left: float = 0.0
    right: float = 1.0
    top: float = 0.0
    bottom: float = 1.0


class JobCreateRequest(BaseModel):
    pages: list[int]                          # 0-indexed page numbers to process
    label_pattern: str = r"LT\d{2,3}[A-Z]?"
    label_prefix: str = "LT"
    detection_mode: str = "thorough"          # fast | thorough
    crop_bounds: CropBoundsSchema | None = None


class DetectionResponse(BaseModel):
    label: str
    circuit: str | None
    room: str | None
    confidence: str
    notes: str | None


class SheetResultResponse(BaseModel):
    page_index: int
    page_label: str
    final_counts: dict
    total: int
    duplicates_removed: int
    pattern_warnings: list
    vlm_calls_used: int
    elapsed_s: float
    detections: list[dict] | None = None
    drawing_context: dict | None = None


class JobResponse(BaseModel):
    id: int
    filename: str
    status: str
    progress: float
    progress_message: str
    error_message: str | None
    label_pattern: str
    detection_mode: str
    pages: str
    vlm_calls_used: int
    phase_log: dict | list | None
    created_at: datetime
    completed_at: datetime | None
    sheets: list[SheetResultResponse] = []


class JobListResponse(BaseModel):
    id: int
    filename: str
    status: str
    progress: float
    progress_message: str
    label_pattern: str
    detection_mode: str
    vlm_calls_used: int
    created_at: datetime
    completed_at: datetime | None


# --- PDF Info ---

class PDFInfoResponse(BaseModel):
    upload_id: str
    filename: str
    num_pages: int
    page_labels: list[str]
