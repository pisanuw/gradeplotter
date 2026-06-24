#!/usr/bin/env bash
set -euo pipefail

# Gather files from multiple run subdirectories into one common directory.
# Usage: gather-css-stats.sh <runs-dir> [output-dir]
#
# output-dir defaults to the parent of runs-dir, so
#   css-gather-stats.sh ~/Downloads/Grading\ Statistics/runs
# places files into ~/Downloads/Grading\ Statistics/.

RUNS_DIR="${1:?Usage: css-gather-stats.sh <runs-dir> [output-dir]}"
OUTPUT_DIR="${2:-$(dirname "$RUNS_DIR")}"

if [[ ! -d "$RUNS_DIR" ]]; then
    echo "ERROR: runs directory does not exist: $RUNS_DIR" >&2
    exit 1
fi

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

# Pass 1: write "run_id TAB rel_path" for every file worth gathering,
# then sort by rel_path so identical paths land in adjacent lines.
while IFS= read -r -d '' run_dir; do
    run_id="$(basename "$run_dir")"
    while IFS= read -r -d '' file; do
        rel="${file#./}"
        # Skip run-specific metadata and macOS junk.
        # .sha256 sidecars are written to output_root/.skip_cache/, not inside
        # run directories, so they should not appear here; skip defensively anyway.
        [[ "$rel" == "manifest.json" ]]                        && continue
        [[ "$rel" == ".DS_Store" || "$rel" =~ /\.DS_Store$ ]] && continue
        [[ "$rel" == *.sha256 ]]                               && continue
        printf '%s\t%s\n' "$run_id" "$rel"
    done < <(cd "$run_dir" && find . -type f -print0 | sort -z)
done < <(find "$RUNS_DIR" -maxdepth 1 -mindepth 1 -type d -print0 | sort -z) \
    | sort -t$'\t' -k2,2 -k1,1 > "$TMPFILE"

moved=0
already_present=0
conflicts=0

# Process one group (all runs that contain the same rel_path).
process_group() {
    local rel="$1"
    shift
    local run_ids=("$@")

    local dst="$OUTPUT_DIR/$rel"
    local srcs=()
    local run_id
    for run_id in "${run_ids[@]}"; do
        srcs+=("$RUNS_DIR/$run_id/$rel")
    done

    local reference="${srcs[0]}"
    local all_identical=true

    local dst_exists=false
    [[ -e "$dst" ]] && dst_exists=true

    local src
    for src in "${srcs[@]:1}"; do
        if ! cmp -s "$reference" "$src"; then
            all_identical=false
            break
        fi
    done
    if $all_identical && $dst_exists; then
        cmp -s "$reference" "$dst" || all_identical=false
    fi

    if $all_identical; then
        if $dst_exists; then
            # Already gathered on a previous run; just clean up the run copies.
            for src in "${srcs[@]}"; do
                rm "$src"
            done
            already_present=$(( already_present + 1 ))
        else
            mkdir -p "$(dirname "$dst")"
            mv "$reference" "$dst"
            for src in "${srcs[@]:1}"; do
                rm "$src"
            done
            moved=$(( moved + 1 ))
        fi
    else
        echo "CONFLICT: $rel"
        for src in "${srcs[@]}"; do
            echo "    $src"
        done
        $dst_exists && echo "    $dst  (already in output)"
        conflicts=$(( conflicts + 1 ))
    fi
}

# Pass 2: read sorted temp file, accumulate lines with the same rel_path,
# and call process_group whenever the rel_path changes.
prev_rel=""
run_ids=()

while IFS=$'\t' read -r run_id rel; do
    if [[ "$rel" != "$prev_rel" && -n "$prev_rel" ]]; then
        process_group "$prev_rel" "${run_ids[@]}"
        run_ids=()
    fi
    prev_rel="$rel"
    run_ids+=("$run_id")
done < "$TMPFILE"

# Handle the final group.
if [[ -n "$prev_rel" ]]; then
    process_group "$prev_rel" "${run_ids[@]}"
fi

echo ""
echo "Moved: $moved  Already present (run copies removed): $already_present  Conflicts (left in place): $conflicts"
