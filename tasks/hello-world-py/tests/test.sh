#!/bin/bash

VERIFIER_DIR="/logs/verifier"

# --- Setup ---
# All verifier tooling (python3, pytest) is baked into the environment image
# at build time. The runtime has no network: do not apt-get / pip / curl here.
echo "verifier tooling preinstalled in image" >>"$VERIFIER_DIR/setup-stdout.txt"

# --- Run test suite ---
# Disable errexit so a failing suite still lets us write reward.txt.
# Suite output goes to suite-stdout.txt (not Harbor's combined test-stdout.txt).
#
# Harbor starts this script in the image WORKDIR (/app) — the directory the
# agent has been writing to all episode. `python3 -m` puts that cwd first on
# sys.path, so a stray /app/pathlib.py (or json.py, csv.py, ...) left by the
# agent would be imported by the suite in place of the stdlib and could forge
# a passing run. `cd /tests` and `-P` keep the agent's directory off the
# import path; `-p no:cacheprovider` stops pytest writing .pytest_cache into
# /tests. Flag order matters: `-p no:cacheprovider` is a pytest option and
# must come after `-m pytest` — before it, Python dies on "Unknown option:
# -p" and every trial (the oracle included) scores 0.
set +e
{
  cd /tests && python3 -P -m pytest -p no:cacheprovider test_outputs.py
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
