from __future__ import annotations

import concurrent.futures
from typing import Callable, Any

import sentry_sdk
from flask import Flask
from itsdangerous import URLSafeSerializer

try:
    import redis
    from rq import Queue
except Exception:  # pragma: no cover - optional in dev
    redis = None
    Queue = None  # type: ignore


class TaskBackend:
    def __init__(self) -> None:
        self.queue: Queue | None = None
        self.executor: concurrent.futures.ThreadPoolExecutor | None = None

    def init_app(self, app: Flask) -> None:
        use_rq = app.config.get("USE_RQ", True) and app.config.get("REDIS_URL")
        if use_rq and redis and Queue:
            rconn = redis.from_url(app.config["REDIS_URL"])  # type: ignore[arg-type]
            self.queue = Queue("essential-tools", connection=rconn)
        else:
            # Fallback to threadpool for dev/testing
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def enqueue(self, func: Callable[..., Any], *args: Any, **kwargs: Any):
        if self.queue:
            return self.queue.enqueue(func, *args, **kwargs)
        else:
            # Simple async submit; returns a Future-like object
            return self.executor.submit(func, *args, **kwargs)  # type: ignore[return-value]


task_backend = TaskBackend()
signer: URLSafeSerializer | None = None


def init_extensions(app: Flask) -> None:
    global signer
    # Sentry (optional)
    dsn = app.config.get("SENTRY_DSN")
    if dsn:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.1)

    # Task system
    task_backend.init_app(app)

    # Download link signer
    signer = URLSafeSerializer(app.config["SECRET_KEY"], salt="essential-tools-download")
