from __future__ import annotations

import html
import os
from html.parser import HTMLParser
from typing import Dict, List, Tuple

_WEASY_AVAILABLE = None  # lazy-checked at runtime


PAGE_SIZES_CSS = {
    "a4": "210mm 297mm",
    "letter": "8.5in 11in",
    "legal": "8.5in 14in",
    "tabloid": "11in 17in",
    "continuous": "210mm 1000mm",
}

PAGE_SIZES_PT: Dict[str, Tuple[float, float]] = {
    "a4": (595.28, 841.89),
    "letter": (612, 792),
    "legal": (612, 1008),
    "tabloid": (792, 1224),
    "continuous": (595.28, 2000.0),
}


def _build_styles(page_size: str) -> str:
    size = PAGE_SIZES_CSS.get(page_size, PAGE_SIZES_CSS["a4"])
    margin = "20mm" if page_size != "continuous" else "15mm"
    return f"""
    @page {{ size: {size}; margin: {margin}; }}
    body {{ font-family: 'Helvetica', sans-serif; font-size: 12pt; }}
    pre {{ font-family: 'Courier New', monospace; white-space: pre-wrap; word-break: break-word; }}
    code {{ font-family: 'Courier New', monospace; }}
    """


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []

    def handle_starttag(self, tag: str, attrs):  # type: ignore[override]
        if tag in {"br", "p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str):  # type: ignore[override]
        if tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data: str):  # type: ignore[override]
        if data:
            self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts)


def _html_to_text(content: str) -> str:
    parser = _TextExtractor()
    parser.feed(content)
    return "\n".join(line.strip() for line in parser.get_text().splitlines())


def _wrap_lines(text: str, max_width: float, font: str, size: float) -> List[str]:
    import fitz  # type: ignore

    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    line = ""
    for word in words:
        candidate = (line + " " + word) if line else word
        if fitz.get_text_length(candidate, fontname=font, fontsize=size) <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def _render_with_fitz(content: str, page_size: str, mode: str, out_path: str) -> None:
    import fitz  # type: ignore

    width, height = PAGE_SIZES_PT.get(page_size, PAGE_SIZES_PT["a4"])
    margin = 54  # 0.75 inch
    font = "courier" if mode == "source" else "helv"
    size = 11 if font == "helv" else 9
    line_height = size * 1.5

    if mode == "source":
        text = content
    else:
        text = _html_to_text(content)

    paragraphs = text.splitlines() or [""]

    max_width = width - 2 * margin

    # Precompute wrapped lines to determine height for continuous mode
    wrapped_paragraphs: List[List[str]] = []
    total_lines = 0
    for para in paragraphs:
        para = para.rstrip()
        lines = _wrap_lines(para if para else " ", max_width, font, size) or [""]
        wrapped_paragraphs.append(lines)
        total_lines += len(lines) + 1  # include spacing

    if page_size == "continuous":
        height = max(height, margin * 2 + line_height * total_lines)

    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    y = margin

    for lines in wrapped_paragraphs:
        for line in lines:
            if y + line_height > height - margin:
                page = doc.new_page(width=width, height=height)
                y = margin
            page.insert_text((margin, y), line, fontname=font, fontsize=size)
            y += line_height
        y += line_height * 0.5

    doc.save(out_path)
    doc.close()


def process(job, upload_paths: List[str]) -> Dict[str, List[str]]:
    html_content = job.options.get("html") or ""
    if not html_content and upload_paths:
        with open(upload_paths[0], "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

    if not html_content.strip():
        raise ValueError("Provide HTML content or upload an HTML file")

    mode = (job.options.get("mode") or "render").lower()
    page_size = (job.options.get("page_size") or "a4").lower()

    if mode == "source":
        escaped = html.escape(html_content)
        body = f"<h1 style=\"font-family:Helvetica,sans-serif;\">HTML Source</h1><pre>{escaped}</pre>"
    else:
        content = html_content
        lower = content.lower()
        if "<html" not in lower:
            content = f"<html><head><meta charset='utf-8'></head><body>{content}</body></html>"
        body = content

    out_name = f"{job.id}_html.pdf"
    out_path = os.path.join(job.workspace_path, out_name)
    rendered = False

    global _WEASY_AVAILABLE
    if _WEASY_AVAILABLE is None:
        # Only attempt to import WeasyPrint when first used, to avoid startup warnings
        try:
            from weasyprint import HTML as _WHTML, CSS as _WCSS  # type: ignore
            _WEASY_AVAILABLE = (_WHTML, _WCSS)
        except Exception:
            _WEASY_AVAILABLE = False

    if _WEASY_AVAILABLE not in (False, None):
        try:
            _WHTML, _WCSS = _WEASY_AVAILABLE  # type: ignore[misc]
            css = _build_styles(page_size)
            _WHTML(string=body, base_url=os.getcwd()).write_pdf(out_path, stylesheets=[_WCSS(string=css)])
            rendered = True
        except Exception:
            rendered = False

    if not rendered:
        # Fall back to simple text rendering via PyMuPDF
        _render_with_fitz(html_content, page_size, mode, out_path)

    return {"files": [out_path]}
