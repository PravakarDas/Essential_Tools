from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "tiff", "bmp", "doc", "docx", "ppt", "pptx"}


def allowed_file(filename: str, allowed: set[str] | None = None) -> bool:
    allowed = allowed or ALLOWED_EXTENSIONS
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def save_uploads(workspace: str, files: Iterable, subdir: str = "uploads") -> list[str]:
    out_dir = os.path.join(workspace, subdir)
    os.makedirs(out_dir, exist_ok=True)
    paths: list[str] = []
    for f in files:
        # Werkzeug FileStorage
        filename = os.path.basename(f.filename)
        if not allowed_file(filename):
            raise ValueError(f"Unsupported file type: {filename}")
        clean = secure_filename(filename)
        path = os.path.join(out_dir, clean)
        f.save(path)
        paths.append(path)
    return paths


def secure_filename(name: str) -> str:
    # Minimal implementation to avoid pulling Werkzeug's helper explicitly
    keep = [c for c in name if c.isalnum() or c in (".", "-", "_", " ")]
    cleaned = "".join(keep).strip().replace(" ", "_")
    return cleaned or "file"


def clean_workspace(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def temp_pdf_path(workspace: str, name: str) -> str:
    Path(workspace).mkdir(parents=True, exist_ok=True)
    return os.path.join(workspace, name)
