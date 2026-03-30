# gradeplotter

This repository now contains two implementations:

- Legacy scripts:
	- `grade-analyzer.py`
	- `grade_analyzer_globals.py`
	- `grade_analyzer_plotter.py`
- New rewrite scaffold (v2):
	- `gradeplotter_v2/`
	- `run_v2_generate.py`
	- `run_v2_app.py`

## v2 goals

- Replace monolithic global-state script with modular services.
- Preserve behavior parity for graph generation (histograms and multiyear trends).
- Add run manifests and artifact indexing.
- Provide simple role-based local web app (Admin vs Viewer).

## Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-v2.txt
```

## Generate artifacts (v2)

```bash
source .venv/bin/activate
python run_v2_generate.py \
	-i 2020AUT-2021SUM.csv \
	--dest gradeplotter_output \
	--curriculum CSS
```



Optional flags:

- `--instructor '.*'`
- `--sections '.*'`
- `--after 2024AUT`
- `--before 2025AUT`
- `--no-histograms`
- `--no-multiyear`
- `--multiyear-instructor`
- `--combosections` (single histogram for all sections per course)
- `--comboinstructor` (single histogram for all sections per course per instructor)
- `--dfwreport <course>` (generate drop/fail/withdraw/repeat report for a course)

Artifacts and manifests are written to:

- `gradeplotter_output/runs/<RUN_ID>/...`
- `gradeplotter_output/runs/<RUN_ID>/manifest.json`
- `gradeplotter_output/latest-manifest.json`

## Run local web app (v2)

```bash
source .venv/bin/activate
python run_v2_app.py
```

Open `http://127.0.0.1:5000`.

Default credentials (override via env vars):

- Admin: `admin` / `admin`
- Viewer: `viewer` / `viewer`

Supported environment variables:

- `GRADEPLOTTER_SECRET_KEY`
- `GRADEPLOTTER_OUTPUT_ROOT`
- `GRADEPLOTTER_ADMIN_USER`
- `GRADEPLOTTER_ADMIN_PASSWORD`
- `GRADEPLOTTER_VIEWER_USER`
- `GRADEPLOTTER_VIEWER_PASSWORD`

## Current rewrite status

Implemented:

- Header-based CSV loading and typed domain models.
- Filtering/query repository for curriculum/instructor/section/term bounds.
- Histogram and multiyear rendering pipeline with manifest output.
- Legacy-style graph output layout for parity: byYear, byInstructor, byCourse, and stats_per_course paths inside each run.
- Legacy-style section filename formatting and --sections matching against compact names.
- Quarter-aware date filtering parity for --after/--before semantics.
- Flask app with login, gallery, run history, and admin generation form.
- Decision/questions tracking in `Todo.md`.

Not yet implemented:

- Full parity for every legacy report mode (`--func`, `--dfwreport`, progression/workload outputs).
- Legacy path-duplication compatibility layer.
- Production-ready auth backend and audit logging.