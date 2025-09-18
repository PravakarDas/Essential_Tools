from __future__ import annotations

import io
import os
from typing import Dict, List

from PIL import Image  # type: ignore


ALIGN_MAP = {"left": 0.15, "center": 0.5, "right": 0.85}


def _prepare_signature(path: str, remove_bg: bool, threshold: int = 220):
    img = Image.open(path).convert("RGBA")
    if remove_bg:
        pixels = []
        for r, g, b, a in img.getdata():
            if r >= threshold and g >= threshold and b >= threshold:
                pixels.append((r, g, b, 0))
            else:
                pixels.append((r, g, b, a))
        img.putdata(pixels)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), img.width, img.height


def _select_pages(total: int, mode: str) -> List[int]:
    if total == 0:
        return []
    mode = (mode or "all").lower()
    if mode == "first":
        return [0]
    if mode == "last":
        return [total - 1]
    return list(range(total))


def process(job, upload_paths: List[str]) -> Dict[str, List[str]]:
    import fitz  # type: ignore

    pdf_path = None
    sig_path = None
    for path in upload_paths:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            pdf_path = path
        elif ext in {".png", ".jpg", ".jpeg", ".bmp"}:
            sig_path = path

    if not pdf_path or not sig_path:
        raise ValueError("Upload both PDF and signature image")

    remove_bg = bool(job.options.get("remove_bg"))
    placement = job.options.get("placement", "all")
    align = job.options.get("align", "right").lower()
    align_factor = ALIGN_MAP.get(align, ALIGN_MAP["right"])
    scale = float(job.options.get("scale", 0.3))
    scale = min(max(scale, 0.1), 0.6)

    sig_stream, sig_w_px, sig_h_px = _prepare_signature(sig_path, remove_bg)

    doc = fitz.open(pdf_path)
    target_pages = _select_pages(doc.page_count, placement)
    if not target_pages:
        raise ValueError("No pages selected for signing")

    margin = 36  # half inch

    for idx in target_pages:
        page = doc[idx]
        rect = page.rect
        sig_width = rect.width * scale
        sig_height = sig_width * (sig_h_px / sig_w_px)
        if sig_height > rect.height * 0.3:
            sig_height = rect.height * 0.3
            sig_width = sig_height * (sig_w_px / sig_h_px)

        x_center = rect.x0 + rect.width * align_factor
        x0 = x_center - sig_width / 2
        if x0 < rect.x0 + margin:
            x0 = rect.x0 + margin
        x1 = x0 + sig_width
        if x1 > rect.x1 - margin:
            x1 = rect.x1 - margin
            x0 = x1 - sig_width
        y1 = rect.y1 - margin
        y0 = y1 - sig_height

        page.insert_image(fitz.Rect(x0, y0, x1, y1), stream=sig_stream, overlay=True)

    out_name = f"{job.id}_signed.pdf"
    out_path = os.path.join(job.workspace_path, out_name)
    doc.save(out_path)
    doc.close()

    return {"files": [out_path]}
