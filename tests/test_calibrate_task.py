import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CALIBRATE = ROOT / "scripts" / "calibrate-task.sh"
COMMIT = "d" * 40


class CalibrateTaskTests(unittest.TestCase):
    def test_runs_harbor_with_the_default_calibration_target(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        task_dir = temp_dir / "example-task"
        task_dir.mkdir()
        (task_dir / "task.toml").write_text('schema_version = "1.3"\n')
        jobs_dir = temp_dir / "jobs"
        bin_dir = temp_dir / "bin"
        bin_dir.mkdir()
        fake_harbor = bin_dir / "harbor"
        fake_harbor.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
[[ "$*" == *"-a terminus-2"* ]]
[[ "$*" == *"-m gemini/gemini-3.8-flash"* ]]
[[ "$*" == *"-k 10"* ]]
for i in {0..9}; do
  mkdir -p "$HARBOR_JOBS_DIR/run-$i/verifier"
  if [[ "$i" -lt 2 ]]; then echo 1; else echo 0; fi > "$HARBOR_JOBS_DIR/run-$i/verifier/reward.txt"
done
"""
        )
        fake_harbor.chmod(0o755)
        env_file = temp_dir / ".env"
        env_file.write_text("GEMINI_API_KEY=test\n")
        environment = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "HARBOR_JOBS_DIR": str(jobs_dir),
        }

        result = subprocess.run(
            [
                "bash",
                str(CALIBRATE),
                str(task_dir),
                "--commit",
                COMMIT,
                "--env-file",
                str(env_file),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(
            (task_dir / "calibration" / "results.json").read_text()
        )
        self.assertEqual(record["commit"], COMMIT)
        self.assertEqual(record["model"], "gemini/gemini-3.8-flash")
        self.assertEqual(record["success_count"], 2)
        self.assertTrue(record["accepted"])


    def test_runs_harbor_with_a_custom_calibration_target(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        task_dir = temp_dir / "example-task"
        task_dir.mkdir()
        (task_dir / "task.toml").write_text('schema_version = "1.3"\n')
        target_file = temp_dir / "target.json"
        target_file.write_text(
            json.dumps(
                {
                    "agent": "terminus-2",
                    "model": "example/designated-model",
                    "attempt_count": 10,
                    "min_success": 1,
                    "max_success": 4,
                }
            )
        )
        jobs_dir = temp_dir / "jobs"
        bin_dir = temp_dir / "bin"
        bin_dir.mkdir()
        fake_harbor = bin_dir / "harbor"
        fake_harbor.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
[[ "$*" == *"-a terminus-2"* ]]
[[ "$*" == *"-m example/designated-model"* ]]
[[ "$*" == *"-k 10"* ]]
for i in {0..9}; do
  mkdir -p "$HARBOR_JOBS_DIR/run-$i/verifier"
  if [[ "$i" -lt 2 ]]; then echo 1; else echo 0; fi > "$HARBOR_JOBS_DIR/run-$i/verifier/reward.txt"
done
"""
        )
        fake_harbor.chmod(0o755)
        env_file = temp_dir / ".env"
        env_file.write_text("EXAMPLE_API_KEY=test\n")
        environment = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "HARBOR_JOBS_DIR": str(jobs_dir),
        }

        result = subprocess.run(
            [
                "bash",
                str(CALIBRATE),
                str(task_dir),
                "--commit",
                COMMIT,
                "--env-file",
                str(env_file),
                "--target",
                str(target_file),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(
            (task_dir / "calibration" / "results.json").read_text()
        )
        self.assertEqual(record["model"], "example/designated-model")
        self.assertEqual(record["attempt_count"], 10)
        self.assertEqual(record["success_count"], 2)
        self.assertTrue(record["accepted"])


class CalibrationTargetTests(unittest.TestCase):
    # LiteLLM resolves the provider from the prefix. A model string with an
    # unknown prefix fails with "LLM Provider NOT provided" before any container
    # starts, so every attempt errors out and no task can ever be calibrated.
    KNOWN_PREFIXES = {
        "gemini",
        "vertex_ai",
        "openrouter",
        "anthropic",
        "openai",
        "bedrock",
        "azure",
        "xai",
    }

    def test_pinned_model_uses_a_known_provider_route(self) -> None:
        target = json.loads((ROOT / "calibration-target.json").read_text())
        model = target["model"]
        self.assertIn("/", model, f"model {model!r} has no provider prefix")
        prefix = model.split("/", 1)[0]
        self.assertIn(prefix, self.KNOWN_PREFIXES, f"unknown provider route {model!r}")


if __name__ == "__main__":
    unittest.main()
