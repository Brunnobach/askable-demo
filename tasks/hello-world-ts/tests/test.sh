#!/bin/bash

VERIFIER_DIR="/logs/verifier"

# --- Setup ---
# bun and react/react-dom are provided by the environment image (see
# environment/Dockerfile). Ensure bun is on PATH for non-login shells.
{
  export BUN_INSTALL="${BUN_INSTALL:-/root/.bun}"
  export PATH="$BUN_INSTALL/bin:$PATH"
} >>"$VERIFIER_DIR/setup-stdout.txt" 2>&1

# --- Run test suite ---
# Guard against errexit so a failing suite still lets us write reward.txt,
# even if Harbor invokes this script under `set -e`.
# Suite output goes to suite-stdout.txt (not Harbor's combined test-stdout.txt).
#
# Harbor starts this script in the image WORKDIR (/app) — the directory the
# agent has been writing to all episode — and bun reads bunfig.toml (including
# [test].preload, which executes arbitrary scripts inside the test process)
# from its cwd. `cd /tests` first so the agent cannot plant configuration the
# verifier will load. Bare imports are safe either way: they resolve from the
# test file's directory upward (/tests, /), never through /app.
set +e
{
  cd /tests && bun test ./test_outputs.ts
} >>"$VERIFIER_DIR/suite-stdout.txt" 2>&1
TEST_EXIT=$?
set -e

# --- Write reward from suite exit code ---
# Harbor grades on reward.txt (1 = pass, 0 = fail). Do not change the exit
# status of this script based on TEST_EXIT; only the reward file matters.
if [ $TEST_EXIT -eq 0 ]; then
  echo 1 >"$VERIFIER_DIR/reward.txt"
else
  echo 0 >"$VERIFIER_DIR/reward.txt"
fi
