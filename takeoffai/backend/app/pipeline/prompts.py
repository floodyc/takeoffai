"""TakeoffAI — Prompt templates for all pipeline phases.

All VLM prompts are centralized here for easy tuning.
"""


# ── Phase 1: Context Extraction ──────────────────────────────────────────────

CONTEXT_EXTRACTION_PROMPT = """You are an expert electrical drawing analyst.
You are looking at a full-page electrical floor plan rendered at low resolution.

Extract the following information:
1. Sheet number and title (e.g., "E6 - Level 3 Floor Plan")
2. Building type and floor level
3. All suite/room numbers visible and their approximate locations
   (top-left, top-right, center-left, center-right, bottom-left, bottom-right, etc.)
4. Corridor layout description (L-shaped, double-loaded, single-loaded, U-shaped, etc.)
5. Stair and elevator locations
6. Title block info if visible: architect, engineer, project name
7. Fixture label types you can see on the drawing (e.g., LT04, LT07, LT11)

Return ONLY valid JSON with this structure:
{
  "sheet_number": "E6",
  "sheet_title": "Level 3 Floor Plan, Lighting, Power and Low Tension",
  "building_type": "residential",
  "floor_level": 3,
  "suites": [
    {"number": "301", "location": "bottom-right", "type": "1 BED 1 BATH"},
    {"number": "307", "location": "top-left", "type": "2 BED 2 BATH"}
  ],
  "corridor_layout": "double-loaded with central elevator lobby",
  "stairs": [{"name": "Stair 1", "location": "center-right"}],
  "elevators": [{"name": "Elev 1", "location": "center"}],
  "title_block": {"architect": "Buttjes Architecture", "engineer": "Jarvis Engineering", "project": "UBC Lot 4"},
  "fixture_types_visible": ["LT04", "LT04A", "LT04B", "LT07", "LT09", "LT11"]
}

If you cannot determine a field, use null. For suites, list ALL you can identify."""


# ── Phase 2: Coarse Detection ────────────────────────────────────────────────

COARSE_DETECTION_PROMPT = """You are an expert electrical drawing analyst performing a lighting fixture takeoff.

DRAWING CONTEXT:
{drawing_context}

You are looking at grid cell ({col}, {row}) of a {grid_cols}×{grid_rows} grid overlay on the floor plan.
This cell covers approximately the {region_description}.

TARGET: Find all oval-shaped labels matching "{label_prefix}" followed by digits and optionally
a letter suffix (e.g., {label_prefix}04, {label_prefix}04A, {label_prefix}11).

WHAT TARGET LABELS LOOK LIKE:
- Small oval/ellipse shape (horizontal or rotated 90°)
- Contains text like "{label_prefix}04", "{label_prefix}11", "{label_prefix}04A", "{label_prefix}04B"
- Usually near a fixture symbol, connected to circuit wiring lines
- May have a circuit designator nearby (e.g., HB-1N/L, EMB-1N/L)

IGNORE:
- Circle symbols with single letters: (T), (F), ($)
- Oval labels that do NOT start with "{label_prefix}" (e.g., FS22, X1, EF-A)
- Receptacle symbols, switch symbols, panel labels
- Any text not inside an oval shape

For each detection, provide:
- label: exact text (e.g., "LT04", "LT04A")
- circuit: circuit designator if visible nearby
- room: room/suite/area it's in (use suite numbers from context if known)
- position: approximate position as percentage from top-left (x%, y%)
- confidence: HIGH (clearly readable), MEDIUM (partially obscured), LOW (inferred)
- on_boundary: true if the label is at or very near the edge of this image crop

Return ONLY valid JSON:
{{
  "detections": [
    {{
      "label": "{label_prefix}04",
      "circuit": "HB-1N/L",
      "room": "corridor",
      "position": {{"x": 45, "y": 62}},
      "confidence": "HIGH",
      "on_boundary": false,
      "notes": "clear label, recessed downlight symbol"
    }}
  ],
  "other_fixtures_seen": ["LT07", "LT11"],
  "cell_description": "Suite 307 kitchen and living area"
}}

If NO matching labels found, return: {{"detections": [], "other_fixtures_seen": [], "cell_description": "..."}}"""


# ── Phase 3: Orchestrator System Prompt ──────────────────────────────────────

ORCHESTRATOR_SYSTEM_PROMPT = """You are an expert electrical drawing analyst orchestrating a lighting fixture takeoff.

You have completed Phase 1 (context extraction) and Phase 2 (coarse grid detection).
Now you are in Phase 3: Agentic Refinement. Your job is to improve detection accuracy.

DRAWING CONTEXT:
{drawing_context}

CURRENT DETECTION STATE:
{detection_state}

VLM BUDGET: {remaining_calls} calls remaining. Use them wisely.

YOUR REFINEMENT STRATEGY:
1. Check for MISSING fixtures using validate_pattern. Each suite kitchen should have
   at least one fixture of each variant (e.g., LT04A + LT04B). Corridor fixtures should
   follow consistent patterns.

2. Re-inspect BOUNDARY zones where fixtures may have been split across grid cells.
   Focus on boundary detections flagged in Phase 2.

3. Re-inspect LOW CONFIDENCE detections at higher resolution to confirm or reject them.

4. Do NOT re-inspect areas with only HIGH confidence detections — they're fine.

5. When satisfied the count is accurate, call finalize with a summary.

IMPORTANT:
- Start by calling validate_pattern to identify gaps
- Then use crop_and_inspect for targeted re-inspection
- Each crop_and_inspect costs 1 VLM call from your budget
- Be strategic — inspect the highest-value areas first"""


# ── Phase 3: Refinement Detection Prompt ─────────────────────────────────────

REFINEMENT_DETECTION_PROMPT = """You are re-inspecting a specific region of an electrical floor plan at high resolution.

DRAWING CONTEXT:
{drawing_context}

REASON FOR RE-INSPECTION: {reason}
TARGET FIXTURE: {target_fixture}

Count EVERY instance of {target_fixture} (and variants like {target_fixture}A, {target_fixture}B)
in this image. Be thorough — this is a targeted re-inspection to catch fixtures that may
have been missed in an earlier coarse scan.

For each fixture, provide:
- label: exact label text (e.g., LT04, LT04A, LT04B)
- circuit: circuit designator if visible
- room: room/area identifier
- confidence: HIGH/MEDIUM/LOW
- notes: any relevant details

Return ONLY valid JSON:
{{
  "detections": [
    {{"label": "...", "circuit": "...", "room": "...", "confidence": "...", "notes": "..."}}
  ],
  "region_summary": "brief description of what's in this crop"
}}

If NO matching fixtures found, return: {{"detections": [], "region_summary": "..."}}"""
