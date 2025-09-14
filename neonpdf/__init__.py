import os
from flask import Flask
from .config import Config
from .extensions import init_extensions
from .blueprints.main import bp as main_bp
from .api.jobs import bp as api_jobs_bp


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True, static_folder="static", template_folder="templates")

    # Ensure instance folder exists (for per-job workspaces)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Load config
    app.config.from_object(Config())
    if test_config:
        app.config.update(test_config)

    # Ensure jobs dir exists
    os.makedirs(app.config["JOBS_DIR"], exist_ok=True)

    # Extensions and services
    init_extensions(app)

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_jobs_bp, url_prefix="/api")


    return app

