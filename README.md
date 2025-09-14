# neonpdf (Flask)

neonpdf is a Flask-based toolkit for common PDF tasks (merge, split, rotate, convert, sign, protect, etc.), inspired by iLovePDF. It features a modern neon UI, light/dark mode, responsive grid, a clean API, and background workers (RQ/Redis or thread fallback) for heavy jobs.

## Quickstart

- Create venv and install deps
  - Windows: `python -m venv .venv && .venv\\Scripts\\activate`
  - Unix/Mac: `python -m venv .venv && source .venv/bin/activate`
  - Install: `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and adjust variables as needed.
- Run dev server: `python run.py`
- Optional worker (Redis + RQ): set `REDIS_URL` in `.env`, then `python worker/rq_worker.py`

System binaries (for advanced tools) you should install later: Poppler, wkhtmltopdf, LibreOffice, Ghostscript, qpdf.

## Project layout

- `neonpdf/__init__.py`: `create_app()` factory, blueprints, healthcheck
- `neonpdf/api/jobs.py`: Job API for create/status/delete/download
- `neonpdf/models/job.py`: Filesystem-backed Job model (JSON per job)
- `neonpdf/tasks/jobs.py`: Background tasks (merge/split/rotate implemented)
- `neonpdf/static/`: Neon CSS + JS (dark/light toggle)
- `neonpdf/templates/`: Base layout, tools grid, generic tool page
- `worker/rq_worker.py`: RQ worker entrypoint

Jobs are stored under `instance/jobs/<job_id>` with a `job.json` manifest and any generated files. A signed URL allows downloading artifacts via `/api/download/...`.

## API

- `POST /api/jobs` form-data or JSON: `{ tool, options, files[] }` → `{ job_id }`
- `GET /api/jobs/<id>` → job status and results
- `DELETE /api/jobs/<id>` → remove job workspace
- `GET /api/download/<id>/<token>/<filename>` → one-time signed download
- `GET /healthz` → health check

## Implemented tools (initial)

- Merge PDF (pypdf)
- Split PDF by ranges (pypdf)
- Rotate PDF pages (pypdf)

Other tools are scaffolded at the UI level and can be implemented incrementally under `neonpdf/tasks/` and service wrappers.

## Notes

- In development without Redis, tasks run on a thread pool automatically.
- For production, run behind Gunicorn + Nginx and use Redis + RQ or Celery.
- Configure TTL cleanup with a cron/Celery beat later (not included in this scaffold).

## License

Proprietary or TBD — add your preferred license.
