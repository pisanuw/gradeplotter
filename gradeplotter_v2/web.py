from __future__ import annotations

from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, session, url_for

from .config import load_config
from .generator import GenerationOptions, generate_artifacts
from .indexer import collect_artifacts, load_manifests


def _require_role(*roles: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = session.get("role")
            if role not in roles:
                return redirect(url_for("login"))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def create_app() -> Flask:

    import os
    config = load_config()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, "templates")
    app = Flask(__name__, template_folder=template_dir)
    app.secret_key = config.secret_key

    @app.get("/run/<run_id>")
    @_require_role("admin", "viewer")
    def run_artifacts(run_id: str):
        # Find the manifest for this run
        from .indexer import load_manifests
        manifests = load_manifests(config.output_root)
        manifest = next((m for m in manifests if m.get("run_id") == run_id), None)
        if not manifest:
            abort(404)
        artifacts = manifest.get("artifacts", [])
        return render_template(
            "run_artifacts.html",
            run_id=run_id,
            artifacts=artifacts,
            role=session.get("role"),
        )

    users = {
        config.admin_user: {"password": config.admin_password, "role": "admin"},
        config.viewer_user: {"password": config.viewer_password, "role": "viewer"},
    }

    @app.get("/")
    def root():
        if session.get("role"):
            return redirect(url_for("runs"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            profile = users.get(username)
            if not profile or profile["password"] != password:
                flash("Invalid username or password", "error")
            else:
                session["username"] = username
                session["role"] = profile["role"]
                return redirect(url_for("runs"))
        return render_template("login.html")

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # /gallery route and view removed; use /runs and per-run artifact pages instead

    @app.get("/artifact/<path:artifact_path>")
    @_require_role("admin", "viewer")
    def artifact(artifact_path: str):
        full_path = config.output_root / artifact_path
        if not full_path.exists() or not full_path.is_file():
            abort(404)
        # Ensure absolute path for send_from_directory
        abs_root = str(config.output_root.resolve())
        return send_from_directory(abs_root, artifact_path)

    @app.get("/runs")
    @_require_role("admin", "viewer")
    def runs():
        manifests = load_manifests(config.output_root)
        # Find latest run with artifacts
        latest_records = []
        available_terms = set()
        available_instructors = set()
        if manifests:
            # Try to load records from the latest manifest's input files
            from .loader import load_grade_records
            try:
                input_files = manifests[0].get("inputs", [])
                if input_files:
                    from pathlib import Path
                    records = load_grade_records([Path(p) for p in input_files])
                    latest_records = records
            except Exception:
                pass
        if latest_records:
            # Extract all unique term codes and instructors
            available_terms = sorted({r.section.term.code for r in latest_records})
            available_instructors = sorted({r.section.instructor for r in latest_records})
        return render_template(
            "runs.html",
            manifests=manifests,
            role=session.get("role"),
            available_terms=available_terms,
            available_instructors=available_instructors,
        )

    @app.post("/admin/generate")
    @_require_role("admin")
    def admin_generate():
        input_files_raw = request.form.get("input_files", "")
        input_files = [Path(p.strip()) for p in input_files_raw.splitlines() if p.strip()]
        if not input_files:
            flash("At least one input CSV file is required", "error")
            return redirect(url_for("runs"))

        missing = [str(path) for path in input_files if not path.exists()]
        if missing:
            flash(f"Missing input files: {', '.join(missing)}", "error")
            return redirect(url_for("runs"))

        # Handle multi-select instructor
        instructors = request.form.getlist("instructor")
        if not instructors or ".*" in instructors:
            instructor_pattern = ".*"
        else:
            instructor_pattern = "|".join(instructors)
        options = GenerationOptions(
            input_files=input_files,
            output_root=config.output_root,
            curriculum_pattern=request.form.get("curriculum", "CSS"),
            instructor_pattern=instructor_pattern,
            section_pattern=request.form.get("sections", ".*"),
            after_term_code=request.form.get("after") or None,
            before_term_code=request.form.get("before") or None,
            include_histograms=request.form.get("include_histograms") == "on",
            include_multiyear=request.form.get("include_multiyear") == "on",
            include_instructor_multiyear=request.form.get("include_instructor_multiyear")
            == "on",
        )
        manifest = generate_artifacts(options)
        flash(
            f"Generation complete: run {manifest['run_id']} created {manifest['artifact_count']} artifacts",
            "success",
        )
        return redirect(url_for("runs"))

    return app
