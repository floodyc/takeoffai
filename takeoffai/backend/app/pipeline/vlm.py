"""VLM fixture detection — sends image crops to Claude Vision API.

Phase 2 (coarse detection) and Phase 3 (refinement crops) both use this module.
Key difference from aecai-lt-counter: drawing context is injected into every prompt.
"""

import asyncio
import base64
import json
import logging
import re
from pathlib import Path
from typing import Optional

import anthropic

from .config import PipelineConfig
from .models import CellInfo, Detection, DrawingContext
from .prompts import COARSE_DETECTION_PROMPT, REFINEMENT_DETECTION_PROMPT

logger = logging.getLogger(__name__)


def _encode_image(path: str | Path) -> str:
    """Base64-encode an image file."""
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def _parse_json(text: str) -> dict:
    """Extract JSON from VLM response, handling markdown fences."""
    cleaned = re.sub(r"```json\s*", "", text)
    cleaned = re.sub(r"```\s*", "", cleaned)
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {"detections": [], "other_fixtures_seen": [], "cell_description": "parse error"}


# ── Coarse Detection (Phase 2) ───────────────────────────────────────────────

async def inspect_cell(
    client: anthropic.AsyncAnthropic,
    cell: CellInfo,
    cfg: PipelineConfig,
    context: Optional[DrawingContext],
    semaphore: asyncio.Semaphore,
) -> list[Detection]:
    """Inspect a single grid cell for target fixtures.

    The drawing context is injected into the prompt so the VLM knows
    which area of the building this cell represents.
    """
    # Build context-aware prompt
    ctx_str = json.dumps(context.to_dict(), default=str) if context else "Not available"
    region_desc = (
        context.describe_region(cell.col, cell.row, cfg.coarse_grid_cols, cfg.coarse_grid_rows)
        if context else f"row {cell.row}, column {cell.col}"
    )

    prompt = COARSE_DETECTION_PROMPT.format(
        drawing_context=ctx_str,
        col=cell.col, row=cell.row,
        grid_cols=cfg.coarse_grid_cols, grid_rows=cfg.coarse_grid_rows,
        region_description=region_desc,
        label_prefix=cfg.label_prefix,
    )

    async with semaphore:
        image_data = _encode_image(cell.path)

        for attempt in range(4):
            try:
                response = await client.messages.create(
                    model=cfg.detection_model,
                    max_tokens=cfg.detection_max_tokens,
                    temperature=cfg.detection_temperature,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {
                                "type": "base64", "media_type": "image/png", "data": image_data,
                            }},
                            {"type": "text", "text": prompt},
                        ],
                    }],
                )
                break
            except anthropic.RateLimitError:
                delay = 15 * (2 ** attempt)
                logger.warning(f"Rate limited on {cell.key}, retry in {delay}s")
                await asyncio.sleep(delay)
        else:
            logger.error(f"Rate limit exhausted for {cell.key}")
            return []

        text = response.content[0].text
        data = _parse_json(text)

        detections = []
        for d in data.get("detections", []):
            label = d.get("label", "").upper().strip()
            if not re.match(cfg.label_pattern, label):
                continue

            pos = d.get("position", {})
            if isinstance(pos, dict):
                px = cell.x0 + (pos.get("x", 50) / 100) * (cell.x1 - cell.x0)
                py = cell.y0 + (pos.get("y", 50) / 100) * (cell.y1 - cell.y0)
            else:
                px = (cell.x0 + cell.x1) / 2
                py = (cell.y0 + cell.y1) / 2

            detections.append(Detection(
                label=label,
                variant=label[len(cfg.label_prefix):].lstrip("0123456789") or None,
                circuit=d.get("circuit"),
                room=d.get("room"),
                x=int(px), y=int(py),
                confidence=d.get("confidence", "MEDIUM"),
                on_boundary=d.get("on_boundary", False),
                source_cell=(cell.col, cell.row),
                source_phase=2,
                notes=d.get("notes", ""),
            ))

        return detections


async def inspect_batch(
    cells: list[CellInfo],
    cfg: PipelineConfig,
    context: Optional[DrawingContext] = None,
) -> list[Detection]:
    """Inspect all grid cells concurrently, returning flat detection list."""
    client = anthropic.AsyncAnthropic()
    semaphore = asyncio.Semaphore(cfg.max_concurrent)

    tasks = [inspect_cell(client, cell, cfg, context, semaphore) for cell in cells]
    all_detections = []
    completed = 0

    for coro in asyncio.as_completed(tasks):
        dets = await coro
        completed += 1
        all_detections.extend(dets)
        logger.info(f"Phase 2: {completed}/{len(cells)} cells scanned, {len(dets)} found")

    return all_detections


# ── Refinement Detection (Phase 3) ───────────────────────────────────────────

async def inspect_crop(
    client: anthropic.AsyncAnthropic,
    image_b64: str,
    cfg: PipelineConfig,
    context: Optional[DrawingContext],
    reason: str,
) -> list[dict]:
    """Inspect a targeted crop at high resolution.

    Called by the Phase 3 agent via the crop_and_inspect tool.
    Returns raw detection dicts (the agent converts to Detection objects).
    """
    ctx_str = json.dumps(context.to_dict(), default=str) if context else "Not available"

    prompt = REFINEMENT_DETECTION_PROMPT.format(
        drawing_context=ctx_str,
        reason=reason,
        target_fixture=cfg.label_prefix,
    )

    for attempt in range(3):
        try:
            response = await client.messages.create(
                model=cfg.detection_model,
                max_tokens=cfg.detection_max_tokens,
                temperature=cfg.detection_temperature,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {
                            "type": "base64", "media_type": "image/png", "data": image_b64,
                        }},
                        {"type": "text", "text": prompt},
                    ],
                }],
            )
            break
        except anthropic.RateLimitError:
            await asyncio.sleep(15 * (2 ** attempt))
    else:
        return []

    text = response.content[0].text
    data = _parse_json(text)
    return data.get("detections", [])
