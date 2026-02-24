"""Phase 1: Context Extraction.

Renders the full page at low DPI and sends to Sonnet to extract
drawing metadata: sheet info, suite locations, corridor layout, etc.
This context is injected into all subsequent VLM calls.
"""

import json
import logging
import time

import anthropic

from .config import PipelineConfig
from .models import DrawingContext, PhaseResult
from .prompts import CONTEXT_EXTRACTION_PROMPT
from .rasterize import PageRenderer, image_to_base64

logger = logging.getLogger(__name__)


async def extract_context(
    renderer: PageRenderer,
    cfg: PipelineConfig,
) -> tuple[DrawingContext, PhaseResult]:
    """Run Phase 1: extract drawing context from low-res full page.

    Returns:
        (DrawingContext, PhaseResult) — the context data and phase metrics
    """
    start = time.time()
    phase = PhaseResult(phase=1)

    try:
        # Render full page at low DPI
        img = renderer.render(dpi=cfg.context_dpi)
        img_b64 = image_to_base64(img, max_dim=cfg.max_image_dim)

        # Single VLM call to Sonnet
        client = anthropic.AsyncAnthropic()
        response = await client.messages.create(
            model=cfg.context_model,
            max_tokens=cfg.context_max_tokens,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": CONTEXT_EXTRACTION_PROMPT},
                ],
            }],
        )
        phase.vlm_calls = 1

        # Parse response
        text = response.content[0].text
        data = _parse_json(text)

        if data:
            context = DrawingContext.from_dict(data)
        else:
            logger.warning("Phase 1: Failed to parse context JSON, using defaults")
            context = DrawingContext()

        phase.metadata = {"context": context.to_dict()}

    except Exception as e:
        logger.error(f"Phase 1 failed: {e}")
        context = DrawingContext()
        phase.error = str(e)

    phase.duration_s = time.time() - start
    logger.info(
        f"Phase 1: {context.sheet_title or 'Unknown sheet'}, "
        f"{len(context.suites)} suites, {len(context.fixture_types_visible)} fixture types "
        f"({phase.duration_s:.1f}s)"
    )
    return context, phase


def _parse_json(text: str) -> dict | None:
    """Extract and parse JSON from VLM response."""
    # Strip markdown fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in text
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None
