from __future__ import annotations

import os
from typing import Any, Dict, List


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one PDF to convert")

    # Lazy import to keep base env light unless used
    try:
        from pdf2docx import Converter  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("pdf2docx is required for PDF to Word conversion") from e

    input_pdf = upload_paths[0]
    out_name = f"{job.id}.docx"
    out_path = os.path.join(job.workspace_path, out_name)

    cv = Converter(input_pdf)
    try:
        # Convert all pages; pdf2docx uses 0-based start
        cv.convert(out_path, start=0, end=None)
    finally:
        cv.close()

    return {"files": [out_path]}

