import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARIZER = ROOT / "scripts" / "summarize-calibration.py"
COMMIT = "c" * 40


class SummarizeCalibrationTests(unittest.TestCase):
    def summarize(
        self, rewards: list[int], target: dict | None = None
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        temp_dir = Path(tempfile.mkdtemp())
        rewards_file = temp_dir / "rewards.json"
        output_file = temp_dir / "results.json"
        rewards_file.write_text(json.dumps({"rewards": rewards}))
        command = [
            sys.executable,
            str(SUMMARIZER),
            "--task",
            "example-task",
            "--commit",
            COMMIT,
            "--rewards-file",
            str(rewards_file),
            "--output",
            str(output_file),
        ]
        if target is not None:
            target_file = temp_dir / "target.json"
            target_file.write_text(json.dumps(target))
            command += ["--target", str(target_file)]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        return result, output_file

    def test_accepts_four_successes_from_ten_attempts(self) -> None:
        result, output_file = self.summarize([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(output_file.read_text())
        self.assertEqual(record["success_count"], 4)
        self.assertEqual(record["pass_rate"], 0.4)
        self.assertTrue(record["accepted"])

    def test_rejects_zero_successes(self) -> None:
        result, output_file = self.summarize([0] * 10)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(output_file.exists(), result.stderr)
        self.assertFalse(json.loads(output_file.read_text())["accepted"])

    def test_rejects_five_successes(self) -> None:
        result, output_file = self.summarize([1] * 5 + [0] * 5)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(output_file.exists(), result.stderr)
        self.assertFalse(json.loads(output_file.read_text())["accepted"])

    def test_rejects_reward_count_that_disagrees_with_the_target(self) -> None:
        result, output_file = self.summarize([1] * 4)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output_file.exists())

    def test_honors_a_custom_calibration_target(self) -> None:
        target = {
            "agent": "terminus-2",
            "model": "example/designated-model",
            "attempt_count": 10,
            "min_success": 1,
            "max_success": 4,
        }
        result, output_file = self.summarize([1, 1, 0, 0, 0, 0, 0, 0, 0, 0], target)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(output_file.read_text())
        self.assertEqual(record["model"], "example/designated-model")
        self.assertEqual(record["attempt_count"], 10)
        self.assertEqual(record["success_count"], 2)
        self.assertEqual(record["pass_rate"], 0.2)
        self.assertTrue(record["accepted"])

    def test_rejects_five_successes_under_a_ten_attempt_target(self) -> None:
        target = {
            "agent": "terminus-2",
            "model": "example/designated-model",
            "attempt_count": 10,
            "min_success": 1,
            "max_success": 4,
        }
        result, output_file = self.summarize([1] * 5 + [0] * 5, target)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(json.loads(output_file.read_text())["accepted"])


class SelfCheckRecordTests(unittest.TestCase):
    """A self-check is evidence about a task, never the verdict on one."""

    def _run(self, rewards, self_check):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "rewards.json").write_text(json.dumps({"rewards": rewards}))
        out = tmp / "out.json"
        cmd = [
            sys.executable, str(SUMMARIZER),
            "--task", "example-task", "--commit", "c" * 40,
            "--rewards-file", str(tmp / "rewards.json"),
            "--output", str(out),
        ]
        if self_check:
            cmd.append("--self-check")
        result = subprocess.run(cmd, capture_output=True, text=True)
        record = json.loads(out.read_text()) if out.is_file() else None
        return result, record

    def test_self_check_is_marked_non_authoritative(self):
        result, record = self._run([1, 1, 0, 0, 0, 0, 0, 0, 0, 0], True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(record["authoritative"])

    def test_authoritative_run_is_marked_authoritative(self):
        result, record = self._run([1, 1, 0, 0, 0, 0, 0, 0, 0, 0], False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(record["authoritative"])

    def test_out_of_band_self_check_reports_without_failing(self):
        # 10/10 is an automatic rejection as a measurement, but as a self-check
        # it is a signal to deepen the task, so the command must not fail.
        result, record = self._run([1] * 10, True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(record["accepted"])
        self.assertIn("Deepen the problem", result.stderr)

    def test_out_of_band_authoritative_run_still_fails(self):
        result, _ = self._run([1] * 10, False)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
