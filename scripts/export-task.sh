#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is required but not installed." >&2
    exit 1
  fi
}

usage() {
  echo "Usage: $0 <task-path> [--out <dir>]" >&2
  exit 1
}

TASK_PATH="${1:-}"
[[ -n "$TASK_PATH" ]] || usage
shift

OUT_DIR="$ROOT_DIR/exports"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out)
      OUT_DIR="${2:-}"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

[[ -f "$TASK_PATH/task.toml" ]] || {
  echo "Error: missing task.toml in $TASK_PATH" >&2
  exit 1
}

require_command python3
require_command tar
require_command rsync

CALIBRATION_FILE="$TASK_PATH/calibration/results.json"
COMMIT="UNCALIBRATED"
CALIBRATED="false"
if [[ -f "$CALIBRATION_FILE" ]]; then
  COMMIT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["commit"])' "$CALIBRATION_FILE")"
  CALIBRATED="true"
else
  echo "Warning: no calibration/results.json — exporting an uncalibrated task. Calibration is still required before acceptance." >&2
fi

python3 "$ROOT_DIR/scripts/validate-task-metadata.py" \
  --task "$TASK_PATH" \
  --commit "$COMMIT"

mkdir -p "$OUT_DIR"
STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGE_DIR"' EXIT

TASK_NAME="$(basename "$TASK_PATH")"
EXPORT_STAMP="$(date -u +%Y%m%d)"
ARCHIVE="$OUT_DIR/$TASK_NAME-$EXPORT_STAMP.tar.gz"

rsync -a \
  --exclude ".DS_Store" \
  --exclude "node_modules" \
  --exclude ".git" \
  --exclude "jobs" \
  --exclude "trials" \
  "$TASK_PATH/" "$STAGE_DIR/$TASK_NAME/"

python3 - "$STAGE_DIR/$TASK_NAME" "$CALIBRATED" <<'PY'
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

stage = Path(sys.argv[1])
calibrated = sys.argv[2] == "true"
files = sorted(
    path for path in stage.rglob("*") if path.is_file() and path.name != "manifest.json"
)
manifest = {
    "schema_version": 1,
    "task": stage.name,
    "exported_at": datetime.now(timezone.utc).isoformat(),
    "calibration_present": calibrated,
    "files": [
        {
            "path": str(path.relative_to(stage)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in files
    ],
}
(stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
PY

if [[ -f "$TASK_PATH/calibration/self-check.json" ]]; then
  echo "Note: includes an author self-check (calibration/self-check.json)."
fi

tar -czf "$ARCHIVE" -C "$STAGE_DIR" "$TASK_NAME"

echo "Exported $TASK_NAME to $ARCHIVE"
[[ "$CALIBRATED" == "true" ]] || echo "Reminder: this export is uncalibrated."
