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
  echo "Usage: $0 <task-name>" >&2
  exit 1
fi

TASK_NAME="$1"

harbor tasks init "$TASK_NAME" \
  -p tasks/ \
  --metadata-template templates/askable-task.toml \
  --include-canary-strings

TASK_DIR="tasks/${TASK_NAME}"
mkdir -p "$TASK_DIR/attestations"
cat > "$TASK_DIR/provenance.json" <<'EOF'
{
  "schema_version": 1,
  "third_party_material": []
}
EOF
sed "s/TASK_NAME/${TASK_NAME}/g" templates/contributor-attestation.md \
  > "$TASK_DIR/attestations/YOUR_GITHUB_HANDLE.md"

# Append the calibration harness prerequisites. terminus-2 drives the container
# through tmux; the runtime has no network, so it cannot install them itself and
# every attempt would die before the agent reads the instruction (AUTHORING.md §6).
if [[ -f "$TASK_DIR/environment/Dockerfile" ]] \
  && ! grep -q "tmux" "$TASK_DIR/environment/Dockerfile"; then
  cat >> "$TASK_DIR/environment/Dockerfile" <<'DOCKER'

# Calibration harness: terminus-2 drives the container through tmux and records
# the session with asciinema. Required — without tmux every calibration attempt
# fails before the agent reads the instruction.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tmux asciinema \
    && rm -rf /var/lib/apt/lists/*
DOCKER
fi

# Append the git baseline to the scaffolded Dockerfile so every task starts
# from a committed tree (a GDM-shaped requirement; see AUTHORING.md §6).
if [[ -f "$TASK_DIR/environment/Dockerfile" ]] \
  && ! grep -q "git init" "$TASK_DIR/environment/Dockerfile"; then
  cat >> "$TASK_DIR/environment/Dockerfile" <<'DOCKER'

# Git baseline: the agent starts from a committed tree. Keep solution
# files and any later state out of this history. Install git for your
# base image if it is not already present.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && git init \
    && git config user.email "task@askable.local" \
    && git config user.name "Task Baseline" \
    && git add -A \
    && git commit -m "Task baseline" --allow-empty
DOCKER
fi

echo ""
echo "Created ${TASK_DIR}/"
echo "Next steps:"
echo "  1. Edit tasks/${TASK_NAME}/instruction.md (hand-written — see CONTRIBUTING.md)"
echo "  2. Update tasks/${TASK_NAME}/task.toml (name, description, category, languages, ai_tools_used)"
echo "  3. Complete provenance.json and the contributor attestation."
echo "  4. Edit tasks/${TASK_NAME}/environment/Dockerfile, tests/, and solution/"
echo "     - network_mode is \"no-network\": install everything at image build; never download in tests/test.sh"
echo "     - the git baseline and tmux/asciinema blocks in the Dockerfile are required — do not delete them"
echo "  5. Run ./scripts/validate-task.sh tasks/${TASK_NAME}"
