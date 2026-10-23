import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SUBMISSIONS = ROOT / "scripts" / "validate-submissions.sh"


class ValidateSubmissionsTests(unittest.TestCase):
    def test_accepts_the_template_example_without_calibration_record(self) -> None:
        result = subprocess.run(
            ["bash", str(VALIDATE_SUBMISSIONS)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
