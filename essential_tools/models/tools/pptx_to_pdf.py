from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _libreoffice_exe() -> str | None:
    for name in ("soffice", "soffice.bin"):
        p = _which(name)
        if p:
            return p
    return None


def _convert_with_libreoffice(inp: str, out_dir: str) -> str:
    exe = _libreoffice_exe()
    if not exe:
        raise FileNotFoundError("LibreOffice (soffice) not found")
    cmd = [exe, "--headless", "--nologo", "--convert-to", "pdf", "--outdir", out_dir, inp]
    subprocess.run(cmd, check=True)
    base = os.path.splitext(os.path.basename(inp))[0] + ".pdf"
    return os.path.join(out_dir, base)


def _convert_with_powerpoint(inp: str, out_path: str) -> None:
    # Windows-only PowerPoint automation
    import comtypes.client  # type: ignore
    powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
    powerpoint.Visible = 1
    try:
        presentation = powerpoint.Presentations.Open(inp, WithWindow=False)
        try:
            # 32 is ppFixedFormatTypePDF
            presentation.ExportAsFixedFormat(out_path, 2)  # 2=ppFixedFormatTypePDF
        finally:
            presentation.Close()
    finally:
        powerpoint.Quit()


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one PowerPoint file to convert")
    src = upload_paths[0]
    out_name = f"{job.id}.pdf"
    out_path = os.path.join(job.workspace_path, out_name)

    # Try LibreOffice first (cross-platform)
    try:
        if _libreoffice_exe():
            produced = _convert_with_libreoffice(src, job.workspace_path)
            if os.path.abspath(produced) != os.path.abspath(out_path):
                os.replace(produced, out_path)
            return {"files": [out_path]}
    except Exception:
        pass

    # On Windows, try PowerPoint automation via COM
    if sys.platform.startswith("win"):
        try:
            _convert_with_powerpoint(src, out_path)
            return {"files": [out_path]}
        except Exception:
            pass

    raise RuntimeError(
        "Conversion requires LibreOffice (soffice) on PATH or Microsoft PowerPoint (Windows)."
    )

