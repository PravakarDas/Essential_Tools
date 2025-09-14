from __future__ import annotations

from flask import render_template, request
from . import bp


TOOLS = [
    {"slug": "merge", "title": "Merge PDF", "desc": "Combine multiple PDFs into one.", "category": "organize"},
    {"slug": "split", "title": "Split PDF", "desc": "Extract page ranges into new files.", "category": "organize"},
    {"slug": "compress", "title": "Compress PDF", "desc": "Reduce file size with presets.", "category": "optimize"},
    {"slug": "pdf-to-word", "title": "PDF → Word", "desc": "Convert PDF to DOCX.", "category": "convert"},
    {"slug": "pdf-to-pptx", "title": "PDF → PowerPoint", "desc": "Pages to slides.", "category": "convert"},
    {"slug": "word-to-pdf", "title": "Word → PDF", "desc": "DOC/DOCX to PDF.", "category": "convert"},
    {"slug": "pptx-to-pdf", "title": "PowerPoint → PDF", "desc": "PPT/PPTX to PDF.", "category": "convert"},
    {"slug": "annotate", "title": "Edit/Annotate PDF", "desc": "Add text, highlights, shapes.", "category": "edit"},
    {"slug": "pdf-to-images", "title": "PDF → Images", "desc": "Export pages as JPG/PNG.", "category": "convert"},
    {"slug": "images-to-pdf", "title": "Images → PDF", "desc": "One page per image.", "category": "convert"},
    {"slug": "sign", "title": "Sign PDF", "desc": "Draw/type/upload signature.", "category": "secure"},
    {"slug": "watermark", "title": "Watermark", "desc": "Text or image watermark.", "category": "edit"},
    {"slug": "rotate", "title": "Rotate PDF", "desc": "Rotate pages 90/180/270.", "category": "organize"},
    {"slug": "html-to-pdf", "title": "HTML → PDF", "desc": "URL or HTML to PDF.", "category": "convert"},
    {"slug": "unlock", "title": "Unlock PDF", "desc": "Remove password (with key).", "category": "secure"},
    {"slug": "protect", "title": "Protect PDF", "desc": "Add password & permissions.", "category": "secure"},
]


@bp.get("/")
def index():
    q = request.args.get("q", "").strip().lower()
    tools = TOOLS
    if q:
        tools = [t for t in TOOLS if q in t["title"].lower() or q in t["desc"].lower()]
    return render_template("index.html", tools=tools)


@bp.get("/tool/<slug>")
def tool(slug: str):
    tool = next((t for t in TOOLS if t["slug"] == slug), None)
    if not tool:
        from flask import abort

        abort(404)
    return render_template("tool.html", tool=tool)
