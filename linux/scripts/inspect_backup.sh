#!/bin/sh
# Inspect a private Backup.bin offline without exposing property values or IDs.
set -eu
REPO_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$REPO_DIR"

if [ ! -x .venv/bin/python ]; then
    echo "missing .venv; run scripts/setup.sh" >&2
    exit 1
fi
exec .venv/bin/python -B host/zve10_backup_info.py "$@"
