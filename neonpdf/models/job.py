from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Any, Dict


STATUSES = ("queued", "running", "done", "error")


@dataclass
class Job:
    id: str
    tool: str
    status: str = "queued"
    progress: int = 0
    options: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: time.time())
    finished_at: float | None = None
    workspace_path: str | None = None
    result_manifest: Dict[str, Any] | None = None
    error_message: str | None = None
    user_id: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def new(cls, jobs_dir: str, tool: str, options: Dict[str, Any] | None = None) -> "Job":
        job_id = uuid.uuid4().hex
        workspace = os.path.join(jobs_dir, job_id)
        os.makedirs(workspace, exist_ok=True)
        job = cls(id=job_id, tool=tool, options=options or {}, workspace_path=workspace)
        job.save()
        return job

    @classmethod
    def load(cls, jobs_dir: str, job_id: str) -> "Job":
        jobfile = os.path.join(jobs_dir, job_id, "job.json")
        with open(jobfile, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def save(self) -> None:
        if not self.workspace_path:
            raise RuntimeError("workspace_path not set")
        jobfile = os.path.join(self.workspace_path, "job.json")
        with open(jobfile, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

