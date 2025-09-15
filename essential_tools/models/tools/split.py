from __future__ import annotations

import os
from typing import Any, Dict, List
from pypdf import PdfReader, PdfWriter


def _parse_ranges(expr: str, total_pages: int):
    parts = [p.strip() for p in expr.split(",") if p.strip()]
    for p in parts:
        if "-" in p:
            a_raw, b_raw = p.split("-", 1)
            a = a_raw.strip()
            b = b_raw.strip()
            start = int(a) if a.isdigit() else 1
            end = int(b) if b.isdigit() else total_pages
        else:
            s = p.strip()
            if not s.isdigit():
                continue
            start = end = int(s)
        start = max(1, start)
        end = min(total_pages, end)
        if start <= end:
            yield start, end


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one PDF to split")
    reader = PdfReader(upload_paths[0])
    ranges = job.options.get("ranges") or "1-end"
    outputs: list[str] = []
    ranges_list = list(_parse_ranges(ranges, len(reader.pages)))
    if not ranges_list:
        raise ValueError("Invalid ranges")
    multi = len(ranges_list) > 1
    for idx, (start, end) in enumerate(ranges_list, start=1):
        writer = PdfWriter()
        for i in range(start - 1, end):
            writer.add_page(reader.pages[i])
        if multi:
            out_name = f"splited_part{idx}.pdf"
        else:
            out_name = "splited.pdf"
        out_path = os.path.join(job.workspace_path, out_name)
        with open(out_path, "wb") as f:
            writer.write(f)
        outputs.append(out_path)
    return {"files": outputs}
