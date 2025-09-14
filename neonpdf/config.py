import os
import tempfile


class Config:
    def __init__(self) -> None:
        # Defaults with env overrides
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
        self.MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 100 * 1024 * 1024))  # 100 MB
        # Use system temp for ephemeral job storage by default (not in repo/project dir)
        default_jobs = os.path.join(tempfile.gettempdir(), "neonpdf_jobs")
        self.JOBS_DIR = os.path.abspath(os.getenv("JOBS_DIR", default_jobs))
        self.STORAGE_TTL_MINUTES = int(os.getenv("STORAGE_TTL_MINUTES", 60))
        self.REDIS_URL = os.getenv("REDIS_URL", "")
        self.USE_RQ = os.getenv("USE_RQ", "true").lower() in {"1", "true", "yes", "y"}
        self.SENTRY_DSN = os.getenv("SENTRY_DSN", "")
