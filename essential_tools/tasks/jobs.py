from __future__ import annotations

import os
from typing import Dict, Any, List
from pypdf import PdfReader, PdfWriter

from ..models.job import Job
from ..models.tools import get as get_tool


def _update(job: Job, **fields):
    for k, v in fields.items():
        setattr(job, k, v)
    job.save()


def dispatch_tool(job_dict: Dict[str, Any], upload_paths: List[str]):
    # Executed in background (RQ or thread). Avoid Flask app context dependencies.
    job = Job(**job_dict)
    try:
        _update(job, status="running", progress=5)
        tool = get_tool(job.tool)
        if not tool or not tool.processor:
            raise NotImplementedError(f"Tool not implemented: {job.tool}")
        result = tool.processor(job, upload_paths)

        # Build result manifest and mark done
        files = result.get("files", [])
        manifest = []
        for fn in files:
            manifest.append({
                "filename": os.path.basename(fn),
                "size": os.path.getsize(fn),
            })
        _update(
            job,
            status="done",
            progress=100,
            finished_at=(os.path.getmtime(files[0]) if files else None),
            result_manifest={"files": manifest},
        )
    except Exception as e:  # pragma: no cover - background context
        _update(job, status="error", error_message=str(e))


def _parse_ranges(expr: str, total_pages: int):
    # Kept for backward-compat imports; logic moved into models.tools.split
    from ..models.tools.split import _parse_ranges as _ranges
    yield from _ranges(expr, total_pages)
