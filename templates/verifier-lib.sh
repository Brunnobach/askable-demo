#!/bin/bash
# Optional helper for task verifiers. Copy into tests/ and source from test.sh.
#
# Writes setup and test output to separate files under /logs/verifier so
# validate-task.sh can show them independently of language or test runner.

VERIFIER_DIR="${VERIFIER_DIR:-/logs/verifier}"
SETUP_LOG="${VERIFIER_DIR}/setup-stdout.txt"
# Named suite-stdout.txt to avoid colliding with Harbor's test-stdout.txt
# (which captures the entire test.sh process).
SUITE_LOG="${VERIFIER_DIR}/suite-stdout.txt"

verifier_setup() {
  "$@" >>"$SETUP_LOG" 2>&1
}

# Note: this helper runs your command as-is, in whatever directory test.sh
# started in — which Harbor sets to the image WORKDIR (/app), the directory
# the agent controls. Run the suite from /tests with a runner that does not
# trust the cwd (e.g. `cd /tests && python3 -P -m pytest ...`); a runner that
# imports or loads config from the cwd hands the agent code execution inside
# the verifier. See AUTHORING.md §7.
verifier_run_tests() {
  "$@" >>"$SUITE_LOG" 2>&1
}
