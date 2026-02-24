# TakeoffAI

Agentic AI-powered lighting fixture takeoff from electrical drawings.

## How It Works

TakeoffAI uses a 4-phase agentic pipeline to detect and count fixture labels on electrical floor plan PDFs:

1. **Context Extraction** — Understands the drawing (floor level, suite locations, corridor layout)
2. **Coarse Detection** — Scans the drawing in a 4×3 grid with context-aware prompts
3. **Agentic Refinement** — An AI orchestrator decides where to re-inspect at higher resolution
4. **Synthesis** — Deduplicates detections and validates against expected patterns

~25 VLM calls per page (vs 176 in the predecessor), ~60s processing time, higher accuracy.

## Stack

- **Backend**: Python / FastAPI / PostgreSQL
- **Frontend**: React / Vite / Tailwind CSS
- **AI**: Anthropic Claude Vision API (Sonnet + Haiku)
- **Deploy**: Render (backend) + Vercel (frontend)

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
# Set environment variables (see CLAUDE.md)
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## License

Proprietary — Chris Flood / IES
