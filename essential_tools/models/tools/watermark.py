from __future__ import annotations

import io
import os
from typing import Dict, List

from PIL import Image  # type: ignore


FONT_MAP = {
    "Helvetica": {
        (False, False): "helv",
        (True, False): "helv-bold",
        (False, True): "helv-italic",
        (True, True): "helv-bold-italic",
    },
    "Times": {
        (False, False): "times",
        (True, False): "times-bold",
        (False, True): "times-italic",
        (True, True): "times-bold-italic",
    },
    "Courier": {
        (False, False): "courier",
        (True, False): "courier-bold",
        (False, True): "courier-oblique",
        (True, True): "courier-boldoblique",
    },
}


def _prepare_watermark_image(path: str, opacity: float) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    alpha = img.split()[-1]
    alpha = alpha.point(lambda v: int(v * opacity))
    img.putalpha(alpha)
    return img


def _image_to_bytes(img: Image.Image) -> tuple[bytes, int, int]:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), img.width, img.height


def _font_name(font: str, bold: bool, italic: bool) -> str:
    font = font if font in FONT_MAP else "Helvetica"
    return FONT_MAP[font][(bool(bold), bool(italic))]


def _draw_text(page, text: str, font: str, size: float, style: str, bold: bool, italic: bool, underline: bool):
    import fitz  # type: ignore

    fontname = _font_name(font, bold, italic)
    color = (0.6, 0.6, 0.6)
    rect = page.rect

    if style == "tile":
        step_x = fitz.get_text_length(text, fontname=fontname, fontsize=size) + size * 2
        step_y = size * 2.5
        y = rect.y0 + step_y
        while y < rect.y1:
            x = rect.x0 + size
            while x < rect.x1:
                page.insert_text((x, y), text, fontname=fontname, fontsize=size, color=color, overlay=True)
                if underline:
                    page.draw_line((x, y + 2), (x + step_x - size * 1.5, y + 2), color=color, width=1)
                x += step_x
            y += step_y
        return

    angle = 45 if style == "diagonal" else 0
    text_width = fitz.get_text_length(text, fontname=fontname, fontsize=size)
    x = rect.x0 + (rect.width - text_width) / 2
    y = rect.y0 + rect.height / 2
    page.insert_text((x, y), text, fontname=fontname, fontsize=size, rotate=angle, color=color, overlay=True)
    if underline and angle == 0:
        y_line = y + 2
        page.draw_line((x, y_line), (x + text_width, y_line), color=color, width=1)


def _apply_image(page, stream: bytes, source_size: tuple[int, int], style: str):
    import fitz  # type: ignore

    width_px, height_px = source_size
    rect = page.rect
    if style == "tile":
        target_w = rect.width / 3
        ratio = width_px / height_px
        target_h = target_w / ratio
        y = rect.y0
        while y < rect.y1:
            x = rect.x0
            while x < rect.x1:
                box = fitz.Rect(x, y, x + target_w, y + target_h)
                page.insert_image(box, stream=stream, overlay=True)
                x += target_w + 10
            y += target_h + 10
    else:
        if style == "stretch":
            page.insert_image(rect, stream=stream, overlay=True)
            return
        target_w = rect.width * 0.5
        ratio = width_px / height_px
        target_h = target_w / ratio
        if target_h > rect.height * 0.6:
            target_h = rect.height * 0.6
            target_w = target_h * ratio
        x0 = rect.x0 + (rect.width - target_w) / 2
        y0 = rect.y0 + (rect.height - target_h) / 2
        box = fitz.Rect(x0, y0, x0 + target_w, y0 + target_h)
        page.insert_image(box, stream=stream, overlay=True)


def process(job, upload_paths: List[str]) -> Dict[str, List[str]]:
    import fitz  # type: ignore

    pdf_path = None
    image_path = None
    for path in upload_paths:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            pdf_path = path
        elif ext in {".png", ".jpg", ".jpeg", ".bmp"}:
            image_path = path

    if not pdf_path:
        raise ValueError("Upload a PDF to watermark")

    mode = job.options.get("mode") or ("image" if image_path else "text")
    style = (job.options.get("style") or "diagonal").lower()
    doc = fitz.open(pdf_path)

    if mode == "image":
        if not image_path:
            raise ValueError("Upload a watermark image or choose text mode")
        opacity = float(job.options.get("opacity", 0.2))
        opacity = min(max(opacity, 0.05), 1.0)
        base_img = _prepare_watermark_image(image_path, opacity)
        if style == "diagonal":
            styled_img = base_img.rotate(45, expand=True, resample=Image.BICUBIC)
        else:
            styled_img = base_img
        img_stream, w_px, h_px = _image_to_bytes(styled_img)
        for page in doc:
            _apply_image(page, img_stream, (w_px, h_px), style)
    else:
        text = job.options.get("text", "CONFIDENTIAL") or "CONFIDENTIAL"
        font = job.options.get("font", "Helvetica")
        size = float(job.options.get("size", 48))
        bold = bool(job.options.get("bold"))
        italic = bool(job.options.get("italic"))
        underline = bool(job.options.get("underline"))
        for page in doc:
            _draw_text(page, text, font, size, style, bold, italic, underline)

    out_name = f"{job.id}_watermark.pdf"
    out_path = os.path.join(job.workspace_path, out_name)
    doc.save(out_path)
    doc.close()

    return {"files": [out_path]}
