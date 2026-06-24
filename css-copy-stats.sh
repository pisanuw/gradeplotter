#!/usr/bin/env bash
set -euo pipefail

A="${1:?Usage: css-copy-stats.sh <source-dir> <dest-dir>}"
B="${2:?Usage: css-copy-stats.sh <source-dir> <dest-dir>}"

if [[ ! -d "$A" ]]; then
    echo "ERROR: source directory does not exist: $A" >&2
    exit 1
fi
if [[ ! -d "$B" ]]; then
    echo "ERROR: destination directory does not exist: $B" >&2
    exit 1
fi

copied=0
skipped=0
only_in_b=0

# Pass 1: walk A, copy to B when missing or different.
while IFS= read -r -d '' file; do
    rel="${file#./}"
    src="$A/$rel"
    dst="$B/$rel"

    if [[ ! -e "$dst" ]]; then
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        echo "COPIED (new):     $rel"
        (( copied++ ))
    elif ! cmp -s "$src" "$dst"; then
        cp "$src" "$dst"
        echo "COPIED (updated): $rel"
        (( copied++ ))
    else
        (( skipped++ ))
    fi
done < <(cd "$A" && find . -type f -print0 | sort -z)

# Pass 2: walk B, report files that have no counterpart in A.
while IFS= read -r -d '' file; do
    rel="${file#./}"
    if [[ ! -e "$A/$rel" ]]; then
        echo "ONLY IN B:        $rel"
        (( only_in_b++ ))
    fi
done < <(cd "$B" && find . -type f -print0 | sort -z)

echo ""
echo "Copied: $copied  Skipped (identical): $skipped  Only in B: $only_in_b"
