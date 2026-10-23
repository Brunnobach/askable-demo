#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JOBS_DIR="${HARBOR_JOBS_DIR:-$ROOT_DIR/jobs}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is required but not installed." >&2
    exit 1
  fi
}

usage() {
  echo "Usage: $0 <task-path> --commit <task-code-commit> [--env-file <path>] [--target <path>] [--self-check]" >&2
  exit 1
}

TASK_PATH="${1:-}"
[[ -n "$TASK_PATH" ]] || usage
shift

COMMIT=""
ENV_FILE="$ROOT_DIR/.env"
TARGET_FILE="$ROOT_DIR/calibration-target.json"
SELF_CHECK=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit)
      COMMIT="${2:-}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --target)
      TARGET_FILE="${2:-}"
      shift 2
      ;;
    --self-check)
      SELF_CHECK=1
      shift
      ;;
    *)
      usage
      ;;
  esac
done

[[ -n "$COMMIT" ]] || usage
[[ -f "$TASK_PATH/task.toml" ]] || {
  echo "Error: missing task.toml in $TASK_PATH" >&2
  exit 1
}
[[ -f "$ENV_FILE" ]] || {
  echo "Error: environment file not found: $ENV_FILE" >&2
  exit 1
}
[[ -f "$TARGET_FILE" ]] || {
  echo "Error: calibration target file not found: $TARGET_FILE" >&2
  exit 1
}

require_command harbor
require_command python3

CAL_AGENT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["agent"])' "$TARGET_FILE")"
CAL_MODEL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["model"])' "$TARGET_FILE")"
CAL_ATTEMPTS="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["attempt_count"])' "$TARGET_FILE")"

mkdir -p "$JOBS_DIR"
SNAPSHOT_FILE="$(mktemp)"
REWARDS_FILE="$(mktemp)"
trap 'rm -f "$SNAPSHOT_FILE" "$REWARDS_FILE"' EXIT

python3 "$ROOT_DIR/scripts/collect-calibration-rewards.py" \
  --jobs-dir "$JOBS_DIR" \
  --snapshot-out "$SNAPSHOT_FILE"

harbor run \
  -p "$TASK_PATH" \
  -a "$CAL_AGENT" \
  -m "$CAL_MODEL" \
  -k "$CAL_ATTEMPTS" \
  --env-file "$ENV_FILE"

python3 "$ROOT_DIR/scripts/collect-calibration-rewards.py" \
  --jobs-dir "$JOBS_DIR" \
  --snapshot "$SNAPSHOT_FILE" \
  --expected "$CAL_ATTEMPTS" \
  --output "$REWARDS_FILE"

# results.json is reserved for Askable's authoritative run, so an author
# self-check lands beside it under its own name. Both can coexist; only
# results.json binds attestations in validate-submissions.sh.
if [[ $SELF_CHECK -eq 1 ]]; then
  OUTPUT_FILE="$TASK_PATH/calibration/self-check.json"
  SELF_CHECK_FLAG=(--self-check)
else
  OUTPUT_FILE="$TASK_PATH/calibration/results.json"
  SELF_CHECK_FLAG=()
fi

python3 "$ROOT_DIR/scripts/summarize-calibration.py" \
  --task "$(basename "$TASK_PATH")" \
  --commit "$COMMIT" \
  --rewards-file "$REWARDS_FILE" \
  --target "$TARGET_FILE" \
  "${SELF_CHECK_FLAG[@]+"${SELF_CHECK_FLAG[@]}"}" \
  --output "$OUTPUT_FILE"
