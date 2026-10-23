#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is required but not installed." >&2
    exit 1
  fi
}

require_command python3

shopt -s nullglob
task_dirs=(tasks/*/)
if [[ ${#task_dirs[@]} -eq 0 ]]; then
  echo "Error: no tasks found under tasks/" >&2
  exit 1
fi

for task_dir in "${task_dirs[@]}"; do
  [[ -f "${task_dir}task.toml" ]] || continue
  commit="$(
    python3 - "$task_dir" <<'PY'
import json
import sys
import tomllib
from pathlib import Path

task_dir = Path(sys.argv[1])
with (task_dir / "task.toml").open("rb") as task_file:
    metadata = tomllib.load(task_file).get("metadata", {})
if metadata.get("template_example") is True:
    print("template-example")
    raise SystemExit(0)

results_path = task_dir / "calibration" / "results.json"
if not results_path.is_file():
    # Uncalibrated submissions are a first-class path: Askable runs the
    # authoritative calibration job and adds results.json afterwards.
    print(
        f"Warning: {task_dir} has no calibration/results.json — validating as "
        "an uncalibrated submission (Askable runs the authoritative "
        "calibration).",
        file=sys.stderr,
    )
    print("UNCALIBRATED")
    raise SystemExit(0)

try:
    result = json.loads(results_path.read_text())
    commit = result["commit"]
except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
    print(
        f"Error: {task_dir} has an invalid calibration/results.json: {error}",
        file=sys.stderr,
    )
    raise SystemExit(1)

if not isinstance(commit, str) or not commit.strip():
    print(
        f"Error: {task_dir} calibration/results.json has an invalid commit",
        file=sys.stderr,
    )
    raise SystemExit(1)
print(commit)
PY
  )"
  python3 "$ROOT_DIR/scripts/validate-task-metadata.py" \
    --task "$task_dir" \
    --commit "$commit"
done

echo "All task submission records are valid."
