#!/usr/bin/env bash
set -euo pipefail

# Run from the project root regardless of where this script is called from.
cd "$(dirname "$0")"

DATA_DIR="/Users/pisan/D/admin/gradeData/grades"

# All non-overlapping CSV files covering 2009 to present.
INPUT=(
    "$DATA_DIR/2009-2024SUM-CSS.csv"
    "$DATA_DIR/2024AUT-2025SUM.csv"
    "$DATA_DIR/2025AUTCSS.csv"
    "$DATA_DIR/2026WINCSS.csv"
    "$DATA_DIR/2026SPRCSS.csv"
)

OUTPUT="/Users/pisan/Downloads/Grading Statistics"
CONFIG="instructors.json"

# --skip-unchanged reads a .sha256 sidecar next to each file and skips
# regenerating it when the input data is identical to the previous run.
COMMON=(
    -i "${INPUT[@]}"
    --instructor-config "$CONFIG"
    --dest "$OUTPUT"
    --curriculum CSS
    --skip-unchanged
)

echo "=== Run 1: per-section histograms + course multiyear + per-instructor multiyear ==="
python3 run_v2_generate.py \
    "${COMMON[@]}" \
    --multiyear-instructor

echo ""
echo "=== Run 2: all-sections combined histograms (stats_per_course/{course}-combined.png) ==="
python3 run_v2_generate.py \
    "${COMMON[@]}" \
    --combosections \
    --no-multiyear

echo ""
echo "=== Run 3: per-instructor combined histograms ({course}-combined-{instructor}.png) ==="
python3 run_v2_generate.py \
    "${COMMON[@]}" \
    --comboinstructor \
    --no-multiyear

echo ""
echo "=== All done ==="
