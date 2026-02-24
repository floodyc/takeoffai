"""Phase 4: Synthesis — spatial deduplication and final report.

Replaces the boundary-strip heuristic reconciliation from aecai-lt-counter
with simple spatial deduplication: if two detections of the same label are
within a pixel radius, keep the one with highest confidence.
"""

import logging
from collections import Counter

from .config import PipelineConfig
from .models import Detection, DrawingContext, SynthesisReport

logger = logging.getLogger(__name__)

CONF_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def synthesize(
    detections: list[Detection],
    cfg: PipelineConfig,
    context: DrawingContext | None = None,
) -> SynthesisReport:
    """Deduplicate detections and produce the final report.

    Dedup logic:
    - Sort all detections by confidence (HIGH first)
    - For each detection, check if a kept detection of the same label
      exists within dedup_radius_px pixels
    - If yes: skip (duplicate). If no: keep.
    - Phase 3 detections naturally override Phase 2 because they tend
      to have higher confidence (re-inspected at higher DPI).
    """
    if not detections:
        return SynthesisReport()

    radius = cfg.dedup_radius_px

    # Sort by confidence descending, then by phase (3 before 2 for tie-breaking)
    sorted_dets = sorted(
        detections,
        key=lambda d: (CONF_RANK.get(d.confidence, 0), d.source_phase),
        reverse=True,
    )

    kept: list[Detection] = []
    duplicates = 0

    for det in sorted_dets:
        is_dup = False
        for existing in kept:
            if (existing.label == det.label
                    and abs(existing.x - det.x) < radius
                    and abs(existing.y - det.y) < radius):
                is_dup = True
                break
        if is_dup:
            duplicates += 1
        else:
            kept.append(det)

    # Aggregate counts
    label_counts = Counter(d.label for d in kept)

    # Pattern warnings
    warnings = []
    if context and context.suites:
        warnings.extend(_check_suite_coverage(kept, context, cfg))

    report = SynthesisReport(
        final_counts=dict(sorted(label_counts.items())),
        total=len(kept),
        detections=kept,
        duplicates_removed=duplicates,
        pattern_warnings=warnings,
    )

    logger.info(
        f"Phase 4: {len(kept)} unique detections "
        f"({duplicates} duplicates removed), "
        f"{len(warnings)} warnings"
    )
    return report


def _check_suite_coverage(
    detections: list[Detection],
    context: DrawingContext,
    cfg: PipelineConfig,
) -> list[str]:
    """Check if all suites have expected fixture coverage."""
    warnings = []
    suite_numbers = {s.get("number") for s in context.suites if s.get("number")}
    prefix = cfg.label_prefix

    # Find suites with detections
    detected_suites = set()
    for d in detections:
        room = (d.room or "").lower()
        for sn in suite_numbers:
            if sn.lower() in room:
                detected_suites.add(sn)

    missing = suite_numbers - detected_suites
    if missing:
        warnings.append(
            f"No {prefix} fixtures detected in suites: {', '.join(sorted(missing))}. "
            f"This may indicate missed detections."
        )

    return warnings
