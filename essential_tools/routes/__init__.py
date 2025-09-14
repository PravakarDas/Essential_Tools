from __future__ import annotations

from flask import Flask

from .main import bp as main_bp
from .tools import bp as tools_bp
from .api import bp as api_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(main_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
