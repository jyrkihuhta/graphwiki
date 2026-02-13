#!/usr/bin/env bash
#
# Remove example wiki pages from the data directory.
# These are the sample pages shipped in src/data/pages/.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DATA_DIR="${GRAPHWIKI_DATA_DIR:-$REPO_ROOT/data/pages}"
EXAMPLE_DIR="$REPO_ROOT/src/data/pages"

if [ ! -d "$EXAMPLE_DIR" ]; then
    echo "Example data directory not found: $EXAMPLE_DIR"
    exit 1
fi

if [ ! -d "$DATA_DIR" ]; then
    echo "Data directory not found: $DATA_DIR"
    echo "Nothing to remove."
    exit 0
fi

removed=0
for example_file in "$EXAMPLE_DIR"/*.md; do
    filename="$(basename "$example_file")"
    target="$DATA_DIR/$filename"
    if [ -f "$target" ]; then
        rm "$target"
        echo "Removed: $filename"
        removed=$((removed + 1))
    fi
done

if [ "$removed" -eq 0 ]; then
    echo "No example pages found in $DATA_DIR"
else
    echo "Removed $removed example page(s)."
fi
