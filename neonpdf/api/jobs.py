from __future__ import annotations

import json
import os
from flask import Blueprint, current_app, request, jsonify, url_for, send_from_directory, abort
from ..models.job import Job
from ..extensions import task_backend, signer
from ..utils.files import save_uploads
from ..tasks.jobs import dispatch_tool


bp = Blueprint("api_jobs", __name__)


@bp.post("/jobs")
def create_job():
    tool = request.form.get("tool") or (request.json or {}).get("tool")
    options_raw = request.form.get("options") or (request.json or {}).get("options")
    try:
        options = json.loads(options_raw) if isinstance(options_raw, str) else (options_raw or {})
    except Exception:
        options = {}

    if not tool:
        return jsonify({"error": "Missing tool"}), 400

    job = Job.new(current_app.config["JOBS_DIR"], tool=tool, options=options)

    # Save uploads (form-data)
    files = request.files.getlist("files")
    upload_paths: list[str] = []
    if files:
        upload_paths = save_uploads(job.workspace_path, files)
        job.save()

    # Enqueue background work
    task_backend.enqueue(dispatch_tool, job.to_dict(), upload_paths)

    return jsonify({"job_id": job.id, "status": job.status}), 202


@bp.get("/jobs/<job_id>")
def get_job(job_id: str):
    try:
        job = Job.load(current_app.config["JOBS_DIR"], job_id)
    except FileNotFoundError:
        return jsonify({"error": "Not found"}), 404
    data = job.to_dict()
    # Enrich result manifest with signed URLs at request time
    if signer and data.get("result_manifest") and data["result_manifest"].get("files"):
        files = data["result_manifest"]["files"]
        for f in files:
            fname = f.get("filename")
            if fname and not f.get("url"):
                f["url"] = signed_download_url(job.id, fname)
    return jsonify(data)


@bp.delete("/jobs/<job_id>")
def delete_job(job_id: str):
    workspace = os.path.join(current_app.config["JOBS_DIR"], job_id)
    if not os.path.isdir(workspace):
        return jsonify({"error": "Not found"}), 404
    # Remove workspace
    try:
        import shutil

        shutil.rmtree(workspace, ignore_errors=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True})


# Beacon-friendly delete endpoint
@bp.post("/jobs/<job_id>/delete")
def delete_job_post(job_id: str):
    return delete_job(job_id)


@bp.get("/download/<job_id>/<token>/<filename>")
def download(job_id: str, token: str, filename: str):
    if not signer:
        abort(403)
    try:
        data = signer.loads(token)
        if not (isinstance(data, dict) and data.get("job_id") == job_id and data.get("filename") == filename):
            abort(403)
    except Exception:
        abort(403)
    workspace = os.path.join(current_app.config["JOBS_DIR"], job_id)
    return send_from_directory(workspace, filename, as_attachment=True, download_name=filename)


def signed_download_url(job_id: str, filename: str) -> str:
    token = signer.dumps({"job_id": job_id, "filename": filename})
    return url_for("api_jobs.download", job_id=job_id, token=token, filename=filename, _external=False)
