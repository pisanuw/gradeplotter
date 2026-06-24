# CSS Grading Statistics

Three scripts produce and publish grade histograms and multiyear trend charts
for all CSS courses. Run them in order: generate, gather, copy.

---

## Prerequisites

```bash
pip install -r requirements-v2.txt
```

The scripts assume they are run from the project root (they `cd` there
automatically when invoked).

---

## Step 1 — Generate

```bash
./css-generate-stats.sh
```

Reads all grade CSV files and produces PNG charts in three passes:

| Pass | What it generates | Output location (within each run) |
|------|-------------------|-----------------------------------|
| 1 | Per-section histograms, course multiyear trends, per-instructor multiyear trends | `grading_stats {Name} - {netid}/{Name}/` and `stats_per_course/` |
| 2 | All-sections combined histogram per course | `stats_per_course/{course}-combined.png` |
| 3 | Per-instructor combined histogram per course | `grading_stats {Name} - {netid}/{Name}/{course}-combined-{Name}.png` |

Each run lands in a timestamped subdirectory:

```
~/Downloads/Grading Statistics/runs/20260624T055027Z/
    grading_stats Pisan,Y - pisan/
        Pisan,Y/
            2024-AUT-CSS-143-A-Pisan,Y.png
            CSS143-Pisan,Y.png
            CSS143-combined-Pisan,Y.png
    stats_part_time_instructors/
        Chini,M/
            ...
    stats_per_course/
        CSS142.png
        CSS142-combined.png
    manifest.json
```

`--skip-unchanged` is enabled: if the underlying grade data for a file has not
changed since the last run, that file is skipped. The cache lives in
`~/Downloads/Grading Statistics/.skip_cache/` and persists across runs.

To add or change the input CSV files, or the output directory, edit the
variables at the top of `css-generate-stats.sh`.

**Instructor classification** is controlled by `instructors.json`. Full-time
faculty listed there get their own `grading_stats {Name} - {netid}/` folder;
everyone else goes into `stats_part_time_instructors/`.

---

## Step 2 — Gather

```bash
./css-gather-stats.sh ~/Downloads/Grading\ Statistics/runs
```

Consolidates all timestamped run directories into the parent directory
(`~/Downloads/Grading Statistics/` by default).

```
~/Downloads/Grading Statistics/
    grading_stats Pisan,Y - pisan/
        Pisan,Y/
            2024-AUT-CSS-143-A-Pisan,Y.png   ← moved out of runs/
            ...
    stats_per_course/
        CSS142.png
        ...
    runs/                                     ← emptied (conflicts left here)
```

Rules applied to each file:

| Situation | Action |
|-----------|--------|
| File in one run only | Moved to output directory |
| File in multiple runs, all identical | One copy moved, duplicates deleted |
| File in multiple runs, content differs | Printed as `CONFLICT:`, left in place |
| File already in output directory, matches run copy | Run copy deleted (already present) |
| File already in output directory, content differs | Printed as `CONFLICT:`, left in place |

`manifest.json`, `.DS_Store`, and `.sha256` files are skipped.

A summary is printed at the end:

```
Moved: 847  Already present (run copies removed): 0  Conflicts (left in place): 0
```

---

## Step 3 — Copy to Google Drive

```bash
./css-copy-stats.sh \
  ~/Downloads/Grading\ Statistics \
  "/Users/pisan/Google Drive/Shared drives/CSS Teaching Resources/Grading Statistics"
```

Syncs the gathered output to the shared Google Drive folder. Files are compared
byte-for-byte; only new or changed files are copied.

```
COPIED (new):     stats_per_course/CSS142.png
COPIED (updated): grading_stats Pisan,Y - pisan/Pisan,Y/CSS143-Pisan,Y.png
ONLY IN B:        stats_per_course/CSS100.png   ← exists in Drive but not locally
```

| Line prefix | Meaning |
|-------------|---------|
| `COPIED (new)` | File did not exist in Drive; copied |
| `COPIED (updated)` | File existed but differed; overwritten |
| `ONLY IN B` | File in Drive has no local counterpart; left untouched, printed for review |

A summary is printed at the end:

```
Copied: 12  Skipped (identical): 835  Only in B: 3
```

---

## Typical full workflow

```bash
# 1. Generate (safe to run repeatedly; unchanged files are skipped)
./css-generate-stats.sh

# 2. Consolidate all runs into one directory
./css-gather-stats.sh ~/Downloads/Grading\ Statistics/runs

# 3. Push to Google Drive
./css-copy-stats.sh \
  ~/Downloads/Grading\ Statistics \
  "/Users/pisan/Google Drive/Shared drives/CSS Teaching Resources/Grading Statistics"
```
