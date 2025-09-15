from __future__ import annotations

import os
from typing import Any, Dict, List
from pypdf import PdfReader, PdfWriter


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    
    if len(upload_paths) < 2:
        raise ValueError("Provide at least two PDFs to merge")
    writer = PdfWriter()
    for path in upload_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    out_name = f"{job.id}_merged.pdf"
    out_path = os.path.join(job.workspace_path, out_name)
    with open(out_path, "wb") as f:
        writer.write(f)
    return {"files": [out_path]}
