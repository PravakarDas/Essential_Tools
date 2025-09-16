from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, Dict, List

from pypdf import PdfReader, PdfWriter


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _gs_executable() -> str | None:
    # Try common Ghostscript executables across platforms
    for name in ("gs", "gswin64c", "gswin32c"):
        p = _which(name)
        if p:
            return p
    return None


def _qpdf_executable() -> str | None:
    return _which("qpdf")


def _compress_with_gs(inp: str, out: str, quality: str) -> None:
    # Map UI quality to Ghostscript presets
    preset_map = {
        "low": "/screen",
        "medium": "/ebook",
        "high": "/printer",
    }
    preset = preset_map.get(str(quality).lower(), "/ebook")
    exe = _gs_executable()
    if not exe:
        raise FileNotFoundError("Ghostscript executable not found")
    cmd = [
        exe,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={preset}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={out}",
        inp,
    ]
    subprocess.run(cmd, check=True)


def _compress_with_qpdf(inp: str, out: str) -> None:
    exe = _qpdf_executable()
    if not exe:
        raise FileNotFoundError("qpdf executable not found")
    # Focus on recompressing streams and linearizing for web
    cmd = [
        exe,
        "--linearize",
        "--object-streams=generate",
        "--stream-data=compress",
        inp,
        out,
    ]
    subprocess.run(cmd, check=True)


def _rewrite_with_pypdf(inp: str, out: str) -> None:
    reader = PdfReader(inp)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    with open(out, "wb") as f:
        writer.write(f)


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one PDF to compress")
    input_pdf = upload_paths[0]
    quality = job.options.get("quality", "medium")
    out_name = f"{job.id}_compressed.pdf"
    out_path = os.path.join(job.workspace_path, out_name)

    # Try Ghostscript first, then qpdf, then a simple rewrite fallback.
    tried = []
    try:
        if _gs_executable():
            _compress_with_gs(input_pdf, out_path, quality)
            return {"files": [out_path]}
        tried.append("ghostscript")
    except Exception:
        tried.append("ghostscript")

    try:
        if _qpdf_executable():
            _compress_with_qpdf(input_pdf, out_path)
            return {"files": [out_path]}
        tried.append("qpdf")
    except Exception:
        tried.append("qpdf")

    # Fallback: rewrite with pypdf (minimal size change)
    _rewrite_with_pypdf(input_pdf, out_path)
    return {"files": [out_path]}

