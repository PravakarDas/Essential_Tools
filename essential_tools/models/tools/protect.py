from __future__ import annotations

import os
from typing import Dict, List

import fitz  # type: ignore


def process(job, upload_paths: List[str]) -> Dict[str, List[str]]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one PDF to protect")

    password = (job.options.get("password") or "").strip()
    if not password:
        raise ValueError("Password is required")

    owner_password = (job.options.get("owner_password") or password).strip() or password

    src = upload_paths[0]
    doc = fitz.open(src)
    out_name = f"{job.id}_protected.pdf"
    out_path = os.path.join(job.workspace_path, out_name)

    permissions = 0
    if hasattr(fitz, "PDF_PERM_NONE"):
        permissions = fitz.PDF_PERM_NONE
    else:
        perm_attrs = [
            "PDF_PERM_PRINT",
            "PDF_PERM_MODIFY",
            "PDF_PERM_COPY",
            "PDF_PERM_ANNOTATE",
            "PDF_PERM_FORM",
            "PDF_PERM_ACCESSIBILITY",
            "PDF_PERM_ASSEMBLE",
            "PDF_PERM_PRINT_HIGH",
        ]
        for attr in perm_attrs:
            if hasattr(fitz, attr):
                permissions |= getattr(fitz, attr)

    try:
        doc.save(
            out_path,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw=owner_password,
            user_pw=password,
            permissions=permissions,
        )
    finally:
        doc.close()

    return {"files": [out_path]}
