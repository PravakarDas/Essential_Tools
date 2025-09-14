from __future__ import annotations

from flask import Blueprint, render_template, request
from ..models.tools import all_tools


bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    q = request.args.get("q", "").strip().lower()
    tools = [
        {"slug": t.slug, "title": t.title, "desc": t.desc, "category": t.category}
        for t in all_tools()
    ]
    if q:
        tools = [t for t in tools if q in t["title"].lower() or q in t["desc"].lower()]
    return render_template("index.html", tools=tools)
