from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
import html as html_lib
import xml.etree.ElementTree as ET
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


def process(job, upload_paths: List[str]) -> Dict[str, Any]:
    if len(upload_paths) != 1:
        raise ValueError("Upload exactly one Word file to convert")
    src = upload_paths[0]
    out_name = f"{job.id}.pdf"
    out_path = os.path.join(job.workspace_path, out_name)

    # Convert via LibreOffice (best fidelity; no extra Python libs)
    if _libreoffice_exe():
        produced = _convert_with_libreoffice(src, job.workspace_path)
        if os.path.abspath(produced) != os.path.abspath(out_path):
            os.replace(produced, out_path)
        return {"files": [out_path]}

    # Fallback for DOCX only: stdlib XML parse + PyMuPDF text rendering (no extra libs)
    ext = os.path.splitext(src)[1].lower()
    if ext == ".docx":
        try:
            import fitz  # PyMuPDF
        except Exception as e:  # pragma: no cover
            raise RuntimeError("PyMuPDF is required for DOCX fallback") from e

        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs: list[str] = []
        with zipfile.ZipFile(src, "r") as zf:
            xml_bytes = zf.read("word/document.xml")
            root = ET.fromstring(xml_bytes)
            body = root.find("w:body", ns)
            if body is None:
                raise ValueError("Invalid DOCX: missing body")
            for p in body.findall("w:p", ns):
                texts: list[str] = []
                for el in p:
                    if el.tag == f"{{{ns['w']}}}r":
                        text = "".join((t.text or "") for t in el.findall("w:t", ns))
                        texts.append(text)
                    elif el.tag == f"{{{ns['w']}}}br":
                        texts.append("\n")
                para = "".join(texts).strip()
                if para:
                    paragraphs.append(para)

        # Minimal word-wrap using text width measurement
        def wrap_lines(txt: str, max_width: float, font: str, size: float) -> list[str]:
            words = txt.split()
            lines: list[str] = []
            line = ""
            for w in words:
                candidate = (line + " " + w) if line else w
                if fitz.get_text_length(candidate, fontname=font, fontsize=size) <= max_width:
                    line = candidate
                else:
                    if line:
                        lines.append(line)
                    line = w
            if line:
                lines.append(line)
            return lines

        doc = fitz.open()
        page_size = fitz.paper_rect("a4")
        margin = 72  # 1 inch
        max_width = page_size.width - 2 * margin
        y = margin
        line_height = 16  # px at 12pt with some leading
        font = "helv"
        size = 12
        page = doc.new_page(width=page_size.width, height=page_size.height)
        for para in paragraphs:
            for line in wrap_lines(para, max_width, font, size):
                if y + line_height > page_size.height - margin:
                    page = doc.new_page(width=page_size.width, height=page_size.height)
                    y = margin
                page.insert_text((margin, y), line, fontname=font, fontsize=size)
                y += line_height
            # add a blank line between paragraphs
            y += line_height
        doc.save(out_path)
        doc.close()
        return {"files": [out_path]}

    # If we reach here, no supported engine was available
    raise RuntimeError(
        "This conversion requires LibreOffice (for DOC) or a DOCX file for the built-in fallback."
    )
