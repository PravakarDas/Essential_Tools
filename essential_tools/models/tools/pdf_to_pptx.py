from __future__ import annotations

import io
import os
from typing import Any, Dict, List


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one PDF to convert")

    # Lazy imports to avoid heavy deps unless used
    try:
        import fitz  # PyMuPDF
    except Exception as e:  # pragma: no cover
        raise RuntimeError("pymupdf is required for PDF rendering. Please install 'pymupdf'.") from e

    try:
        from pptx import Presentation  # type: ignore
        from pptx.util import Emu
    except Exception as e:  # pragma: no cover
        raise RuntimeError("python-pptx is required for PowerPoint generation") from e

    input_pdf = upload_paths[0]
    out_name = f"{job.id}.pptx"
    out_path = os.path.join(job.workspace_path, out_name)

    # Render pages to images using PyMuPDF (no external binaries)
    dpi = int(job.options.get("dpi", 150))
    zoom = max(1.0, dpi / 72.0)
    doc = fitz.open(input_pdf)
    if doc.page_count == 0:
        raise ValueError("No pages found in PDF")

    prs = Presentation()
    blank_layout = prs.slide_layouts[6]  # blank
    slide_w = prs.slide_width
    slide_h = prs.slide_height

    for page in doc:
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        buf = io.BytesIO(pix.tobytes("png"))
        slide = prs.slides.add_slide(blank_layout)
        slide.shapes.add_picture(buf, Emu(0), Emu(0), width=slide_w, height=slide_h)

    prs.save(out_path)
    return {"files": [out_path]}
