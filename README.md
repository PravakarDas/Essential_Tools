# Essential Tools (Flask)

Essential Tools is a Flask-based toolkit for common PDF tasks (merge, split, rotate, convert, sign, protect, etc.), inspired by iLovePDF. It features a modern neon UI, light/dark mode, responsive grid, a clean API, and background workers (RQ/Redis or thread fallback) for heavy jobs.

## Quickstart

- Create venv and install deps
  - Windows: `python -m venv .venv && .venv\\Scripts\\activate`
  - Unix/Mac: `python -m venv .venv && source .venv/bin/activate`
  - Install: `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and adjust variables as needed.
- Run dev server: `python run.py`

System binaries (for advanced tools) you should install later: Poppler, wkhtmltopdf, LibreOffice, Ghostscript, qpdf.

## Project layout

- `essential_tools/__init__.py`: `create_app()` factory
- `essential_tools/routes/`: All routing blueprints (`main`, `tools`, `api`)
- `essential_tools/models/job.py`: Filesystem-backed Job model (JSON per job)
- `essential_tools/models/tools/`: Per-tool backends + registry
- `essential_tools/tasks/jobs.py`: Background dispatcher using the registry
- `essential_tools/static/`: CSS + JS
- `essential_tools/templates/`: Base layout, tools grid, per-tool pages under `templates/tools/`
- `worker/rq_worker.py`: RQ worker entrypoint

Jobs are stored under the configured `JOBS_DIR` with a `job.json` manifest and any generated files. A signed URL allows downloading artifacts via `/api/download/...`.

## API

- `POST /api/jobs` form-data or JSON: `{ tool, options, files[] }` → `{ job_id }`
- `GET /api/jobs/<id>` → job status and results
- `DELETE /api/jobs/<id>` → remove job workspace
- `GET /api/download/<id>/<token>/<filename>` → one-time signed download
- `GET /healthz` → health check

## Implemented tools (initial)

- Merge PDF (client-side UI; server impl available)
- Split PDF by ranges (pypdf)
- Rotate PDF pages (pypdf)

Other tools are scaffolded at the UI level and can be implemented incrementally by adding a module under `essential_tools/models/tools/` and registering it.