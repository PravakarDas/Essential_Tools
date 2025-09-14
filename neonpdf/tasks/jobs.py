from __future__ import annotations

import os
from typing import Dict, Any, List
from pypdf import PdfReader, PdfWriter

from ..models.job import Job


def _update(job: Job, **fields):
    for k, v in fields.items():
        setattr(job, k, v)
    job.save()


def dispatch_tool(job_dict: Dict[str, Any], upload_paths: List[str]):
    # Executed in background (RQ or thread). Avoid Flask app context dependencies.
    job = Job(**job_dict)
    try:
        _update(job, status="running", progress=5)
        tool = job.tool
        if tool == "merge":
            result = task_merge(job, upload_paths)
        elif tool == "split":
            result = task_split(job, upload_paths)
        elif tool == "rotate":
            result = task_rotate(job, upload_paths)
        else:
            raise NotImplementedError(f"Tool not implemented: {tool}")

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


def task_merge(job: Job, upload_paths: List[str]) -> Dict[str, Any]:
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


def task_split(job: Job, upload_paths: List[str]) -> Dict[str, Any]:
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


def task_rotate(job: Job, upload_paths: List[str]) -> Dict[str, Any]:
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
