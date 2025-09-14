from __future__ import annotations

import os
from typing import Any, Dict, List
from pypdf import PdfReader, PdfWriter


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one PDF to rotate")
    degrees = int(job.options.get("degrees", 90))
    scope = job.options.get("scope", "all")  # "all" or comma-separated pages
    reader = PdfReader(upload_paths[0])
    writer = PdfWriter()
    if scope == "all":
        targets = set(range(1, len(reader.pages) + 1))
    else:
        targets = set(int(x) for x in str(scope).split(",") if x.strip().isdigit())
    for i, page in enumerate(reader.pages, start=1):
        if i in targets:
            page.rotate(degrees)
        writer.add_page(page)
    out_name = f"{job.id}_rotated.pdf"
    out_path = os.path.join(job.workspace_path, out_name)
    with open(out_path, "wb") as f:
        writer.write(f)
    return {"files": [out_path]}
