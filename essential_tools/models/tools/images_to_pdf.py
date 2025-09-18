from __future__ import annotations

import os
from typing import Any, Dict, List


def _convert_with_img2pdf(paths: List[str], out_path: str) -> None:
    import img2pdf  # type: ignore
    with open(out_path, "wb") as f:
        f.write(img2pdf.convert(paths))


def _convert_with_pillow(paths: List[str], out_path: str) -> None:
    from PIL import Image  # type: ignore
    images: List[Image.Image] = []
    for p in paths:
        img = Image.open(p)
        if img.mode in ("RGBA", "P"):  # remove alpha for PDF
            img = img.convert("RGB")
        images.append(img)
    if not images:
        raise ValueError("No images")
    first, rest = images[0], images[1:]
    first.save(out_path, save_all=True, append_images=rest, format="PDF")
    for img in images:
        img.close()


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if not upload_paths:
        raise ValueError("Upload at least one image")

    # Only accept images; the uploader already filters extensions
    images = list(upload_paths)
    out_name = "images.pdf"
    out_path = os.path.join(job.workspace_path, out_name)

    # Try img2pdf first (produces compact PDFs)
    try:
        _convert_with_img2pdf(images, out_path)
        return {"files": [out_path]}
    except Exception:
        pass

    # Fallback: Pillow
    _convert_with_pillow(images, out_path)
    return {"files": [out_path]}
