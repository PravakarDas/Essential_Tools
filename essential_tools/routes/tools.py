from __future__ import annotations

import os
from flask import Blueprint, render_template, abort
from ..models.tools import get as get_tool


bp = Blueprint("tools", __name__)


@bp.get("/tools/<slug>")
def tool(slug: str):
    tool = get_tool(slug)
    if not tool:
        abort(404)

    # Try specific template at templates/tools/<slug>.html; else show generic coming-soon page
    template_name = f"tools/{slug}.html"
    # Jinja will raise TemplateNotFound if it doesn't exist; handle gracefully
    try:
        return render_template(template_name, tool=tool)
    except Exception:
        return render_template("tools/coming_soon.html", tool=tool), 200
