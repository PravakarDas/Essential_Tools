from __future__ import annotations

import os
from typing import Any, Dict, List
from pypdf import PdfReader, PdfWriter


def _parse_ranges(expr: str, total_pages: int):
    parts = [p.strip() for p in expr.split(",") if p.strip()]
    for p in parts:
        if "-" in p:
            a, b = p.split("-", 1)
            start = int(a) if a.isdigit() else 1
            end = int(b) if b.isdigit() else total_pages
        else:
            start = end = int(p)
        start = max(1, start)
        end = min(total_pages, end)
        if start <= end:
            yield start, end


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one PDF to split")
    reader = PdfReader(upload_paths[0])
    ranges = job.options.get("ranges") or "1-end"  # e.g., "1-3,7,10-end"
    outputs: list[str] = []
    for idx, (start, end) in enumerate(_parse_ranges(ranges, len(reader.pages)), start=1):
        writer = PdfWriter()
        for i in range(start - 1, end):
            writer.add_page(reader.pages[i])
        out_name = f"{job.id}_part{idx}.pdf"
        out_path = os.path.join(job.workspace_path, out_name)
        with open(out_path, "wb") as f:
            writer.write(f)
        outputs.append(out_path)
    return {"files": outputs}
