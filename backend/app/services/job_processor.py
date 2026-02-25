"""Job processing service — orchestrates the 4-phase agentic pipeline."""

import asyncio
import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.pipeline.config import PipelineConfig, CropBounds
from app.pipeline.rasterize import PageRenderer
from app.pipeline.context import extract_context
from app.pipeline.grid import decompose
from app.pipeline.vlm import inspect_batch
from app.pipeline.agent import AgentOrchestrator
from app.pipeline.synthesize import synthesize
from app.pipeline.output import write_xlsx

# Sync DB for background thread
SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "")
sync_engine = create_engine(SYNC_DB_URL, echo=False)
SyncSession = sessionmaker(sync_engine)


def update_job(job_id: int, **kwargs):
    """Update job fields in DB."""
    from app.models.job import Job
    with SyncSession() as db:
        job = db.execute(select(Job).where(Job.id == job_id)).scalar_one()
        for k, v in kwargs.items():
            setattr(job, k, v)
        db.commit()


def process_job_sync(job_id: int):
    """Run the full agentic pipeline. Called from background thread."""
    asyncio.run(_process_job_async(job_id))


async def _process_job_async(job_id: int):
    """Async implementation of the 4-phase pipeline."""
    from app.models.job import Job, SheetResult

    try:
        # Load job config
        with SyncSession() as db:
            job = db.execute(select(Job).where(Job.id == job_id)).scalar_one()
            pages = json.loads(job.pages)
            label_pattern = job.label_pattern
            label_prefix = job.label_prefix or "LT"
            pdf_path = job.upload_path
            detection_mode = job.detection_mode or "thorough"
            crop_bounds_raw = job.crop_bounds

            crop = CropBounds()
            if crop_bounds_raw:
                crop = CropBounds(**crop_bounds_raw)

        update_job(job_id, status="processing", progress=0.0, progress_message="Starting...")

        work_dir = settings.WORK_DIR / f"job_{job_id}"
        work_dir.mkdir(parents=True, exist_ok=True)

        total_pages = len(pages)
        total_vlm_calls = 0
        all_sheet_results = []
        phase_log = []

        for page_idx, page_num in enumerate(pages):
            page_work = work_dir / f"page_{page_num}"
            page_work.mkdir(parents=True, exist_ok=True)

            cfg = PipelineConfig(
                label_pattern=label_pattern,
                label_prefix=label_prefix,
                detection_mode=detection_mode,
                crop=crop,
                work_dir=page_work,
                max_concurrent=settings.MAX_CONCURRENT_VLM,
            )

            base_progress = page_idx / total_pages
            page_frac = 1.0 / total_pages

            renderer = PageRenderer(pdf_path, page_num, cfg)
            page_phases = []

            # ── Phase 1: Context Extraction ───────────────────────────
            update_job(
                job_id,
                progress=base_progress + page_frac * 0.05,
                progress_message=f"Page {page_num + 1}: Phase 1 — Extracting drawing context...",
            )
            print(f"[worker] Job {job_id}: Phase 1 — Context extraction (page {page_num + 1})", flush=True)

            context, phase1 = await extract_context(renderer, cfg)
            page_phases.append({
                "phase": 1,
                "vlm_calls": phase1.vlm_calls,
                "duration_s": phase1.duration_s,
                "error": phase1.error,
            })

            # ── Phase 2: Coarse Detection ─────────────────────────────
            update_job(
                job_id,
                progress=base_progress + page_frac * 0.15,
                progress_message=f"Page {page_num + 1}: Phase 2 — Scanning {cfg.coarse_grid_cells} grid cells...",
            )
            print(f"[worker] Job {job_id}: Phase 2 — {cfg.coarse_grid_cells} cells", flush=True)

            plan_img = renderer.render(dpi=cfg.coarse_dpi)
            grid = decompose(plan_img, cfg)
            coarse_detections = await inspect_batch(grid.cells, cfg, context)

            phase2 = {
                "phase": 2,
                "vlm_calls": len(grid.cells),
                "detections": len(coarse_detections),
            }
            page_phases.append(phase2)

            # ── Phase 3: Agentic Refinement (if thorough mode) ────────
            all_detections = list(coarse_detections)

            if detection_mode == "thorough":
                update_job(
                    job_id,
                    progress=base_progress + page_frac * 0.45,
                    progress_message=f"Page {page_num + 1}: Phase 3 — Agentic refinement...",
                )
                print(f"[worker] Job {job_id}: Phase 3 — Agent refinement", flush=True)

                def on_progress(phase, msg):
                    update_job(job_id, progress_message=f"Page {page_num + 1}: {msg}")

                agent = AgentOrchestrator(
                    renderer=renderer,
                    cfg=cfg,
                    context=context,
                    coarse_detections=coarse_detections,
                    on_progress=on_progress,
                )
                phase3_result = await agent.run()
                all_detections.extend(phase3_result.detections)
                page_phases.append({
                    "phase": 3,
                    "vlm_calls": phase3_result.vlm_calls,
                    "detections": len(phase3_result.detections),
                    "agent_log": phase3_result.metadata.get("agent_log"),
                })

            # ── Phase 4: Synthesis ────────────────────────────────────
            update_job(
                job_id,
                progress=base_progress + page_frac * 0.90,
                progress_message=f"Page {page_num + 1}: Phase 4 — Synthesizing results...",
            )
            print(f"[worker] Job {job_id}: Phase 4 — Synthesis", flush=True)

            report = synthesize(all_detections, cfg, context)

            page_vlm = (
                phase1.vlm_calls
                + len(grid.cells)
                + (phase3_result.vlm_calls if detection_mode == "thorough" else 0)
            )
            total_vlm_calls += page_vlm

            # Store sheet result
            sheet = SheetResult(
                job_id=job_id,
                page_index=page_num,
                page_label=context.sheet_title or f"Page {page_num + 1}",
                final_counts=report.final_counts,
                total=report.total,
                detections=[d.to_dict() for d in report.detections],
                duplicates_removed=report.duplicates_removed,
                pattern_warnings=report.pattern_warnings,
                drawing_context=context.to_dict(),
                agent_log=page_phases,
                vlm_calls_used=page_vlm,
            )
            all_sheet_results.append(sheet)
            phase_log.append({
                "page": page_num,
                "phases": page_phases,
                "total_vlm_calls": page_vlm,
                "final_count": report.total,
            })

            renderer.clear_cache()

        # ── Generate XLSX ─────────────────────────────────────────────
        output_path = settings.OUTPUT_DIR / f"job_{job_id}_results.xlsx"
        # Use the first sheet's report for XLSX (multi-sheet support TBD)
        if all_sheet_results:
            from app.pipeline.reconcile_compat import to_compat_report
            compat = to_compat_report(all_sheet_results[0])
            write_xlsx(compat, output_path, page_label=all_sheet_results[0].page_label)

        # ── Save to DB ────────────────────────────────────────────────
        with SyncSession() as db:
            for sheet in all_sheet_results:
                db.add(sheet)
            db.commit()

        update_job(
            job_id,
            status="completed",
            progress=1.0,
            progress_message="Complete",
            output_path=str(output_path),
            vlm_calls_used=total_vlm_calls,
            phase_log=phase_log,
            completed_at=datetime.now(timezone.utc),
        )
        print(f"[worker] Job {job_id}: COMPLETED ({total_vlm_calls} VLM calls)", flush=True)

    except Exception as e:
        traceback.print_exc()
        print(f"[worker] Job {job_id} FAILED: {e}", flush=True)
        try:
            update_job(
                job_id,
                status="failed",
                error_message=str(e)[:500],
                progress_message=f"Failed: {str(e)[:200]}",
            )
        except Exception:
            pass
