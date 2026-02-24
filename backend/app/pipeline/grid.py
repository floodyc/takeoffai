"""Grid decomposition — simple rectangular grid, no boundary strips.

The agentic pipeline handles boundaries through targeted re-inspection
in Phase 3 instead of pre-computed boundary strips.
"""

from pathlib import Path
from PIL import Image

from .config import PipelineConfig
from .models import CellInfo, GridResult

Image.MAX_IMAGE_PIXELS = None


def decompose(plan_img: Image.Image, cfg: PipelineConfig) -> GridResult:
    """Decompose plan image into a cols×rows grid of cells.

    Args:
        plan_img: PIL Image of the plan area
        cfg: pipeline configuration

    Returns:
        GridResult with cell metadata and saved image paths
    """
    W, H = plan_img.size
    cols = cfg.coarse_grid_cols
    rows = cfg.coarse_grid_rows
    cw = W // cols
    ch = H // rows

    cells_dir = cfg.work_dir / "cells"
    cells_dir.mkdir(parents=True, exist_ok=True)

    cells = []
    for r in range(rows):
        for c in range(cols):
            x0 = c * cw
            y0 = r * ch
            x1 = min(x0 + cw, W)
            y1 = min(y0 + ch, H)

            cell_img = plan_img.crop((x0, y0, x1, y1))
            path = cells_dir / f"r{r}_c{c}.png"
            cell_img.save(str(path))

            cells.append(CellInfo(
                row=r, col=c, path=str(path),
                x0=x0, y0=y0, x1=x1, y1=y1,
            ))

    print(f"[grid] {cols}×{rows} → {len(cells)} cells, cell size {cw}×{ch} px")
    return GridResult(
        cells=cells,
        plan_width=W, plan_height=H,
        cell_width=cw, cell_height=ch,
        cols=cols, rows=rows,
    )
