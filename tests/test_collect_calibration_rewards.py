import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = ROOT / "scripts" / "collect-calibration-rewards.py"


class CollectCalibrationRewardsTests(unittest.TestCase):
    def test_collects_only_new_binary_reward_files(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        jobs_dir = temp_dir / "jobs"
        stale_reward = jobs_dir / "stale" / "verifier" / "reward.txt"
        stale_reward.parent.mkdir(parents=True)
        stale_reward.write_text("1\n")
        snapshot = temp_dir / "before.json"
        output = temp_dir / "rewards.json"

        snapshot_result = subprocess.run(
            [
                sys.executable,
                str(COLLECTOR),
                "--jobs-dir",
                str(jobs_dir),
                "--snapshot-out",
                str(snapshot),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(snapshot_result.returncode, 0, snapshot_result.stderr)
        for index, reward in enumerate([1, 0, 1, 0, 1, 0, 1, 0]):
            reward_file = jobs_dir / f"new-{index}" / "verifier" / "reward.txt"
            reward_file.parent.mkdir(parents=True)
            reward_file.write_text(f"{reward}\n")
        (jobs_dir / "new-0" / "verifier" / "reward.json").write_text(
            json.dumps({"reward": 1})
        )

        result = subprocess.run(
            [
                sys.executable,
                str(COLLECTOR),
                "--jobs-dir",
                str(jobs_dir),
                "--snapshot",
                str(snapshot),
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text()), {"rewards": [1, 0, 1, 0, 1, 0, 1, 0]})


if __name__ == "__main__":
    unittest.main()
