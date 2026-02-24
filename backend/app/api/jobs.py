"""Job endpoints — upload PDF, create jobs, track progress, download results."""

import json
import shutil
import uuid
import threading
from pathlib import Path

import fitz  # PyMuPDF
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.job import Job, SheetResult
from app.api.schemas import (
    JobCreateRequest, JobResponse, JobListResponse,
    SheetResultResponse, PDFInfoResponse,
)
from app.services.job_processor import process_job_sync

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# --- Persistent upload store ---

UPLOADS_INDEX = settings.UPLOAD_DIR / "_uploads.json"


def _load_uploads() -> dict:
    if UPLOADS_INDEX.exists():
        return json.loads(UPLOADS_INDEX.read_text())
    return {}


def _save_uploads(data: dict):
    UPLOADS_INDEX.write_text(json.dumps(data))


def _add_upload(upload_id: str, filepath: str, filename: str, num_pages: int):
    data = _load_uploads()
    data[upload_id] = {"filepath": filepath, "filename": filename, "num_pages": num_pages}
    _save_uploads(data)


def _pop_upload(upload_id: str) -> dict | None:
    data = _load_uploads()
    entry = data.pop(upload_id, None)
    _save_uploads(data)
    return entry


@router.post("/upload", response_model=PDFInfoResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Upload a PDF and get page info back."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    upload_id = uuid.uuid4().hex
    save_path = settings.UPLOAD_DIR / f"{upload_id}.pdf"
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = fitz.open(str(save_path))
    num_pages = len(doc)
    page_labels = []
    for i in range(num_pages):
        page = doc[i]
        text = page.get_text()[:200].strip()
        first_line = text.split("\n")[0][:50] if text else ""
        page_labels.append(f"Page {i + 1}" + (f" — {first_line}" if first_line else ""))
    doc.close()

    _add_upload(upload_id, str(save_path), file.filename, num_pages)

    return PDFInfoResponse(
        upload_id=upload_id,
        filename=file.filename,
        num_pages=num_pages,
        page_labels=page_labels,
    )


@router.post("/create/{upload_id}", response_model=JobResponse)
async def create_job(
    upload_id: str,
    req: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a processing job for an uploaded PDF."""
    upload = _pop_upload(upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found. Please re-upload.")

    filepath = upload["filepath"]
    filename = upload["filename"]
    num_pages = upload["num_pages"]

    for p in req.pages:
        if p < 0 or p >= num_pages:
            raise HTTPException(status_code=400, detail=f"Page {p} out of range (0-{num_pages - 1})")

    import re
    prefix_match = re.match(r"([A-Z]+)", req.label_pattern)
    label_prefix = prefix_match.group(1) if prefix_match else req.label_prefix

    job = Job(
        user_id=user.id,
        filename=filename,
        upload_path=filepath,
        label_pattern=req.label_pattern,
        label_prefix=label_prefix,
        pages=json.dumps(req.pages),
        detection_mode=req.detection_mode,
        crop_bounds=req.crop_bounds.model_dump() if req.crop_bounds else None,
        status="pending",
    )
    db.add(job)
    await db.flush()
    job_id = job.id
    await db.commit()

    print(f"[api] Launching worker thread for job {job_id}", flush=True)
    t = threading.Thread(target=process_job_sync, args=(job_id,), daemon=True)
    t.start()

    return _job_to_response(job, sheets_loaded=False)


@router.get("/", response_model=list[JobListResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Job).where(Job.user_id == user.id).order_by(Job.created_at.desc()).limit(50)
    )
    return [_job_to_list(j) for j in result.scalars()]


@router.delete("/clear")
async def clear_jobs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_job_ids = select(Job.id).where(Job.user_id == user.id)
    await db.execute(delete(SheetResult).where(SheetResult.job_id.in_(user_job_ids)))
    await db.execute(delete(Job).where(Job.user_id == user.id))
    await db.commit()
    return {"detail": "All jobs cleared"}


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Job).options(selectinload(Job.sheets)).where(Job.id == job_id, Job.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job, sheets_loaded=True)


@router.get("/{job_id}/download")
async def download_results(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Job).where(Job.id == job_id, Job.user_id == user.id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.output_path:
        raise HTTPException(status_code=400, detail="Results not ready")

    path = Path(job.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file missing")

    return FileResponse(
        path=str(path),
        filename=f"{Path(job.filename).stem}_takeoff.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# --- Helpers ---

def _job_to_response(job: Job, sheets_loaded: bool = False) -> JobResponse:
    sheets = []
    if sheets_loaded:
        try:
            for s in job.sheets:
                sheets.append(SheetResultResponse(
                    page_index=s.page_index,
                    page_label=s.page_label,
                    final_counts=s.final_counts,
                    total=s.total,
                    duplicates_removed=s.duplicates_removed,
                    pattern_warnings=s.pattern_warnings,
                    vlm_calls_used=s.vlm_calls_used,
                    elapsed_s=s.elapsed_s or 0,
                    detections=s.detections,
                    drawing_context=s.drawing_context,
                ))
        except Exception:
            sheets = []

    return JobResponse(
        id=job.id,
        filename=job.filename,
        status=job.status,
        progress=job.progress,
        progress_message=job.progress_message,
        error_message=job.error_message,
        label_pattern=job.label_pattern,
        detection_mode=job.detection_mode or "thorough",
        pages=job.pages,
        vlm_calls_used=job.vlm_calls_used or 0,
        phase_log=job.phase_log,
        created_at=job.created_at,
        completed_at=job.completed_at,
        sheets=sheets,
    )


def _job_to_list(job: Job) -> JobListResponse:
    return JobListResponse(
        id=job.id,
        filename=job.filename,
        status=job.status,
        progress=job.progress,
        progress_message=job.progress_message,
        label_pattern=job.label_pattern,
        detection_mode=job.detection_mode or "thorough",
        vlm_calls_used=job.vlm_calls_used or 0,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
