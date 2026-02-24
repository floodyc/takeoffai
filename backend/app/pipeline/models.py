"""TakeoffAI Pipeline — Data Models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Detection:
    """A single detected fixture instance."""
    label: str                          # e.g., "LT04", "LT04A", "LT04B"
    variant: Optional[str] = None       # A, B, or None
    circuit: Optional[str] = None       # e.g., "HB-1N/L", "EMB-1N/L"
    room: Optional[str] = None          # e.g., "corridor", "suite 307", "lobby 300"
    x: int = 0                          # pixel position on coarse-DPI rendered page
    y: int = 0
    confidence: str = "MEDIUM"          # HIGH / MEDIUM / LOW
    on_boundary: bool = False           # near a grid cell boundary
    source_cell: Optional[tuple] = None # (col, row) from Phase 2
    source_phase: int = 2               # 2=coarse, 3=refinement
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "variant": self.variant,
            "circuit": self.circuit,
            "room": self.room,
            "x": self.x,
            "y": self.y,
            "confidence": self.confidence,
            "on_boundary": self.on_boundary,
            "source_phase": self.source_phase,
            "notes": self.notes,
        }


@dataclass
class DrawingContext:
    """Metadata extracted from the drawing in Phase 1."""
    sheet_number: Optional[str] = None
    sheet_title: Optional[str] = None
    building_type: Optional[str] = None
    floor_level: Optional[int] = None
    suites: list[dict] = field(default_factory=list)
    corridor_layout: Optional[str] = None
    stairs: list[dict] = field(default_factory=list)
    elevators: list[dict] = field(default_factory=list)
    title_block: dict = field(default_factory=dict)
    fixture_types_visible: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "sheet_number": self.sheet_number,
            "sheet_title": self.sheet_title,
            "building_type": self.building_type,
            "floor_level": self.floor_level,
            "suites": self.suites,
            "corridor_layout": self.corridor_layout,
            "stairs": self.stairs,
            "elevators": self.elevators,
            "title_block": self.title_block,
            "fixture_types_visible": self.fixture_types_visible,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DrawingContext":
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__ if k in data})

    def describe_region(self, col: int, row: int, total_cols: int, total_rows: int) -> str:
        """Generate a human-readable description of what's in a grid region."""
        h_labels = ["left", "center-left", "center-right", "right"]
        v_labels = ["top", "middle", "bottom"]
        h = h_labels[min(col, len(h_labels) - 1)]
        v = v_labels[min(row, len(v_labels) - 1)]
        desc = f"{v} {h} area of the floor plan"

        # Enrich with suite info if available
        if self.suites:
            nearby = [s for s in self.suites if self._location_matches(s.get("location", ""), h, v)]
            if nearby:
                names = ", ".join(f"Suite {s.get('number', '?')}" for s in nearby[:3])
                desc += f" (near {names})"
        return desc

    @staticmethod
    def _location_matches(loc: str, h: str, v: str) -> bool:
        loc = loc.lower()
        return (h.split("-")[0] in loc) or (v in loc)


@dataclass
class CellInfo:
    """Metadata for a single grid cell."""
    row: int
    col: int
    path: str       # path to saved image crop
    x0: int         # pixel bounds on source image
    y0: int
    x1: int
    y1: int

    @property
    def key(self) -> str:
        return f"r{self.row}_c{self.col}"


@dataclass
class GridResult:
    """Grid decomposition output."""
    cells: list[CellInfo]
    plan_width: int
    plan_height: int
    cell_width: int
    cell_height: int
    cols: int
    rows: int


@dataclass
class PhaseResult:
    """Result from a single pipeline phase."""
    phase: int
    detections: list[Detection] = field(default_factory=list)
    vlm_calls: int = 0
    duration_s: float = 0.0
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class SynthesisReport:
    """Final output from Phase 4 synthesis."""
    final_counts: dict[str, int] = field(default_factory=dict)
    total: int = 0
    detections: list[Detection] = field(default_factory=list)
    duplicates_removed: int = 0
    pattern_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "final_counts": self.final_counts,
            "total": self.total,
            "detections": [d.to_dict() for d in self.detections],
            "duplicates_removed": self.duplicates_removed,
            "pattern_warnings": self.pattern_warnings,
        }


@dataclass
class PageResult:
    """Complete result for one drawing page."""
    page_index: int
    context: Optional[DrawingContext] = None
    phases: list[PhaseResult] = field(default_factory=list)
    synthesis: Optional[SynthesisReport] = None
    vlm_calls_total: int = 0
    elapsed_s: float = 0.0

    def to_dict(self) -> dict:
        return {
            "page_index": self.page_index,
            "context": self.context.to_dict() if self.context else None,
            "synthesis": self.synthesis.to_dict() if self.synthesis else None,
            "vlm_calls_total": self.vlm_calls_total,
            "elapsed_s": self.elapsed_s,
            "phase_summary": [
                {"phase": p.phase, "vlm_calls": p.vlm_calls, "duration_s": p.duration_s,
                 "detections": len(p.detections), "error": p.error}
                for p in self.phases
            ],
        }
