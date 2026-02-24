"""TakeoffAI Pipeline Configuration — all tunable parameters in one place."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CropBounds:
    """Fractional crop bounds to isolate plan area from title block/legend."""
    left: float = 0.0
    right: float = 1.0
    top: float = 0.0
    bottom: float = 1.0


@dataclass
class PipelineConfig:
    # --- Phase 1: Context Extraction ---
    context_dpi: int = 72
    context_model: str = "claude-sonnet-4-5-20250514"
    context_max_tokens: int = 2000

    # --- Phase 2: Coarse Detection ---
    coarse_dpi: int = 150
    coarse_grid_cols: int = 4
    coarse_grid_rows: int = 3
    detection_model: str = "claude-haiku-4-5-20251001"
    detection_max_tokens: int = 2000
    detection_temperature: float = 0.0
    max_concurrent: int = 4

    # --- Phase 3: Agentic Refinement ---
    refine_dpi: int = 216
    orchestrator_model: str = "claude-sonnet-4-5-20250514"
    orchestrator_max_tokens: int = 4096
    max_agent_iterations: int = 20
    max_vlm_calls_phase3: int = 15
    max_vlm_calls_total: int = 40  # hard cap across all phases

    # --- Phase 4: Synthesis ---
    dedup_radius_px: int = 50

    # --- Crop ---
    crop: CropBounds = field(default_factory=CropBounds)

    # --- Target labels ---
    label_pattern: str = r"LT\d{2,3}[A-Z]?"
    label_prefix: str = "LT"

    # --- Detection mode ---
    detection_mode: str = "thorough"  # "fast" = Phase 1+2 only, "thorough" = all 4 phases

    # --- I/O ---
    work_dir: Path = Path("./work")
    output_path: Path = Path("./output.xlsx")

    # --- Image constraints ---
    max_image_dim: int = 1568  # Anthropic vision API max recommended dimension

    def __post_init__(self):
        self.work_dir.mkdir(parents=True, exist_ok=True)

    @property
    def coarse_grid_cells(self) -> int:
        return self.coarse_grid_cols * self.coarse_grid_rows

    @property
    def estimated_vlm_calls(self) -> int:
        """Estimate total VLM calls for this config."""
        phase1 = 1
        phase2 = self.coarse_grid_cells
        phase3 = self.max_vlm_calls_phase3 if self.detection_mode == "thorough" else 0
        return phase1 + phase2 + phase3
