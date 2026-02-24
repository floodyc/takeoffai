# TakeoffAI — Project Context

## What This Is

TakeoffAI is an agentic AI-powered fixture takeoff tool for electrical drawings.
It uses Claude Vision to detect and count lighting fixture labels (LT04, LT11, etc.)
on electrical floor plan PDFs.

## Architecture

**4-Phase Agentic Pipeline** (per drawing page):

1. **Phase 1 — Context Extraction** (1 Sonnet VLM call)
   - Renders full page at 72 DPI
   - Extracts: sheet number, floor level, suite locations, corridor layout, fixture types
   - Context is injected into all subsequent VLM calls

2. **Phase 2 — Coarse Detection** (12 Haiku VLM calls)
   - Renders page at 150 DPI, splits into 4×3 grid
   - Each cell sent to Haiku WITH drawing context
   - Returns detections with room, confidence, boundary flags

3. **Phase 3 — Agentic Refinement** (5-15 VLM calls)
   - Sonnet orchestrator in a tool-use loop
   - Reviews Phase 2 results, decides where to re-inspect
   - Tools: crop_and_inspect, validate_pattern, get_current_state, finalize
   - Applies domain knowledge: suite kitchen patterns, corridor symmetry

4. **Phase 4 — Synthesis**
   - Spatial deduplication (50px radius, keep highest confidence)
   - Pattern validation warnings
   - Final structured report

## Stack

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: React (Vite) + Tailwind CSS
- **VLM**: Anthropic Claude Vision API (Sonnet for orchestrator, Haiku for detection)
- **PDF**: PyMuPDF for rendering
- **Deploy**: Render (backend Docker) + Vercel (frontend)

## Key Files

### Pipeline (the core)
- `backend/app/pipeline/config.py` — All tunable parameters
- `backend/app/pipeline/models.py` — Data models (Detection, DrawingContext, etc.)
- `backend/app/pipeline/prompts.py` — All VLM prompt templates
- `backend/app/pipeline/rasterize.py` — PDF → PNG rendering with caching
- `backend/app/pipeline/context.py` — Phase 1: context extraction
- `backend/app/pipeline/grid.py` — Simple rectangular grid (no boundary strips)
- `backend/app/pipeline/vlm.py` — VLM detection calls with context injection
- `backend/app/pipeline/tools.py` — Phase 3 tool definitions
- `backend/app/pipeline/agent.py` — Phase 3 orchestrator loop
- `backend/app/pipeline/synthesize.py` — Phase 4: spatial dedup + validation
- `backend/app/pipeline/output.py` — XLSX report generation

### Infrastructure
- `backend/app/main.py` — FastAPI app
- `backend/app/api/jobs.py` — Job CRUD + upload endpoints
- `backend/app/services/job_processor.py` — Pipeline orchestration + DB updates

## Testing

- **Test PDF**: "UBC Lot 4 IFC (electrical).pdf" (15 pages)
- **Test page**: index 5 (Sheet E6, Level 3)
- **Ground truth for LT04 on page 6**: 28 confirmed, up to 31 total
  - LT04 corridor: 10
  - LT04A kitchens: 8-10
  - LT04B kitchens: 10-11
- **Expected VLM calls per page**: ~25 (vs 176 in aecai-lt-counter)
- **Expected wall time per page**: ~60s (vs ~180s in aecai-lt-counter)

## Config Defaults

```python
CONTEXT_DPI = 72
COARSE_DPI = 150
REFINE_DPI = 216
COARSE_GRID = (4, 3)  # cols × rows
ORCHESTRATOR_MODEL = "claude-sonnet-4-5-20250514"
DETECTION_MODEL = "claude-haiku-4-5-20251001"
MAX_AGENT_ITERATIONS = 20
MAX_VLM_CALLS_PHASE3 = 15
DEDUP_RADIUS_PX = 50
```

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/takeoffai
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=your-jwt-secret
FRONTEND_URL=https://takeoffai.vercel.app
```
