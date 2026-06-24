# Briefing

- Purpose: Generate grade-distribution histograms and multiyear trend charts for CSS courses at UW Bothell, and publish them to a shared Google Drive folder.
- Current scope: Python generator (`run_v2_generate.py` + `gradeplotter_v2/`) produces PNG artifacts; three shell scripts handle generation, consolidation, and sync to Google Drive.
- Key decisions:
  - Output structure mirrors the Google Drive layout: `grading_stats {Name} - {netid}/{Name}/` for full-time faculty, `stats_part_time_instructors/{Name}/` for part-time; course-level files in `stats_per_course/`.
  - Full-time faculty and their netids are declared in `instructors.json`; unknown instructors default to part-time.
  - `--skip-unchanged` uses stable sidecar hashes in `output_root/.skip_cache/` (not next to output files) so the cache persists across timestamped runs.
  - Each generator run lands in a timestamped `runs/{id}/` subdirectory; `css-gather-stats.sh` consolidates them into the parent directory before syncing.
  - Three generator passes are required per update: section histograms + multiyear, combined-per-course, combined-per-instructor.
- Non-goals: The web viewer (`run_v2_app.py`) is out of scope for the current workflow. No deduplication of student records across overlapping CSVs is performed.
