# Changes

Format: `YYYY-MM-DD [type] description` (max 200 chars). Types: decision, plan, doc, scope, code, note.

2026-06-23 [note] Initialized.

2026-06-23 [decision] Output directory structure changed to match Google Drive layout: grading_stats/part-time/stats_per_course instead of byYear/byInstructor/byCourse.

2026-06-23 [decision] Full-time faculty and netids declared in instructors.json; unknown instructors default to stats_part_time_instructors/.

2026-06-23 [code] generator.py: fixed --skip-unchanged; sidecars now stored in output_root/.skip_cache/ keyed by run-relative path so cache persists across timestamped runs.

2026-06-23 [code] generator.py: fixed naming: combined histogram = {course}-combined.png, instructor combined = {course}-combined-{name}.png, course multiyear = stats_per_course/{course}.png.

2026-06-23 [code] Added css-generate-stats.sh (3-pass generate), css-gather-stats.sh (consolidate runs), css-copy-stats.sh (sync to Google Drive).

2026-06-23 [doc] Added css-README.md documenting the generate → gather → copy workflow.
