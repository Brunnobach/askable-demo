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

require_command harbor
require_command docker

shopt -s nullglob
task_dirs=(tasks/*/)

if [[ ${#task_dirs[@]} -eq 0 ]]; then
  echo "Error: no tasks found under tasks/" >&2
  exit 1
fi

for task_dir in "${task_dirs[@]}"; do
  if [[ ! -f "${task_dir}task.toml" ]]; then
    echo "Skipping ${task_dir} (no task.toml)" >&2
    continue
  fi
  ./scripts/validate-task.sh "$task_dir"
done

echo "All tasks validated successfully."
