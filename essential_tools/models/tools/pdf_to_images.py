from __future__ import annotations

import os
import io
import zipfile
from typing import Any, Dict, List


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one PDF")

    try:
        import fitz  # PyMuPDF
    except Exception as e:  # pragma: no cover
        raise RuntimeError("PyMuPDF is required for PDF rendering") from e

    src = upload_paths[0]
    dpi = int(job.options.get("dpi", 150))
    zoom = max(1.0, dpi / 72.0)
    doc = fitz.open(src)
    total = doc.page_count
    if total == 0:
        raise ValueError("Empty PDF")

    img_paths: list[str] = []
    for i, page in enumerate(doc, start=1):
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        name = f"page_{i:03d}.png"
        out_path = os.path.join(job.workspace_path, name)
        pix.save(out_path)
        img_paths.append(out_path)

    # Bundle into a zip archive
    zip_name = "images.zip"
    zip_path = os.path.join(job.workspace_path, zip_name)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in img_paths:
            zf.write(p, arcname=os.path.basename(p))

    return {"files": [zip_path]}

