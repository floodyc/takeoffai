"""Stage: PDF rasterization at configurable DPI with optional crop.

Supports rendering the same page at multiple DPI levels (72, 150, 216)
for different pipeline phases. Caches rendered images to avoid re-rendering.
"""

import base64
import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from .config import PipelineConfig

Image.MAX_IMAGE_PIXELS = None  # Electrical drawings can be very large


class PageRenderer:
    """Renders and caches PDF page images at various DPI levels."""

    def __init__(self, pdf_path: str | Path, page_index: int, cfg: PipelineConfig):
        self.pdf_path = str(pdf_path)
        self.page_index = page_index
        self.cfg = cfg
        self._cache: dict[int, Image.Image] = {}

    def render(self, dpi: int = 150) -> Image.Image:
        """Render the page at a given DPI, with caching."""
        if dpi in self._cache:
            return self._cache[dpi]

        zoom = dpi / 72  # PyMuPDF default is 72 DPI
        doc = fitz.open(self.pdf_path)
        page = doc[self.page_index]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        doc.close()

        # Convert to PIL
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

        # Apply crop bounds if set
        c = self.cfg.crop
        if c.left > 0 or c.right < 1 or c.top > 0 or c.bottom < 1:
            W, H = img.size
            img = img.crop((
                int(W * c.left),
                int(H * c.top),
                int(W * c.right),
                int(H * c.bottom),
            ))

        self._cache[dpi] = img
        return img

    def render_crop(
        self, dpi: int, x_pct: float, y_pct: float, w_pct: float, h_pct: float
    ) -> Image.Image:
        """Render and crop a specific region of the page.

        Args:
            dpi: render resolution
            x_pct, y_pct: center of crop as % (0-100) of page
            w_pct, h_pct: size of crop as % (0-100) of page
        """
        img = self.render(dpi)
        W, H = img.size

        cx = x_pct / 100 * W
        cy = y_pct / 100 * H
        cw = w_pct / 100 * W
        ch = h_pct / 100 * H

        x1 = max(0, int(cx - cw / 2))
        y1 = max(0, int(cy - ch / 2))
        x2 = min(W, int(cx + cw / 2))
        y2 = min(H, int(cy + ch / 2))

        return img.crop((x1, y1, x2, y2))

    def clear_cache(self):
        """Free memory from cached renders."""
        self._cache.clear()


def image_to_base64(img: Image.Image, max_dim: int = 1568) -> str:
    """Encode PIL Image to base64 PNG, downscaling if needed."""
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
