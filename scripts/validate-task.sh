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

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <task-path>" >&2
  exit 1
fi

TASK_PATH="$1"

if [[ ! -d "$TASK_PATH" ]]; then
  echo "Error: task directory not found: $TASK_PATH" >&2
  exit 1
fi

if [[ ! -f "$TASK_PATH/task.toml" ]]; then
  echo "Error: missing task.toml in $TASK_PATH" >&2
  exit 1
fi

echo "Validating task: $TASK_PATH"
TRIAL_OUTPUT="$(harbor trials start -p "$TASK_PATH" -a oracle 2>&1 | tee /dev/stderr)"

TRIAL_NAME="$(printf '%s\n' "$TRIAL_OUTPUT" | sed -n 's/^Trial name: //p' | tail -n 1)"

if [[ -z "$TRIAL_NAME" ]]; then
  echo "Error: could not determine trial name from harbor output" >&2
  exit 1
fi

TRIAL_DIR="./trials/$TRIAL_NAME"

if [[ ! -d "$TRIAL_DIR" ]]; then
  echo "Error: trial output directory not found: $TRIAL_DIR" >&2
  exit 1
fi

REWARD_FILE="$TRIAL_DIR/verifier/reward.txt"
if [[ ! -f "$REWARD_FILE" ]]; then
  REWARD_FILE="$TRIAL_DIR/verifier/reward.json"
fi

print_failure_hints() {
  echo "Inspect failure output with:" >&2
  python3 "$ROOT_DIR/scripts/print-verifier-output.py" "$TRIAL_DIR/verifier" --hints >&2 || true
  echo "  cat $TRIAL_DIR/agent/oracle.txt" >&2
}

if [[ ! -f "$REWARD_FILE" ]]; then
  echo "Error: reward file not found in $TRIAL_DIR/verifier/" >&2
  print_failure_hints
  exit 1
fi

if [[ "$REWARD_FILE" == *.json ]]; then
  REWARD="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['reward'])" "$REWARD_FILE")"
else
  REWARD="$(tr -d '[:space:]' < "$REWARD_FILE")"
fi

if [[ "$REWARD" != "1" && "$REWARD" != "1.0" ]]; then
  echo "Error: oracle validation failed (reward=$REWARD, expected 1)" >&2
  print_failure_hints
  exit 1
fi

echo "OK: $TASK_PATH (reward=1)"
