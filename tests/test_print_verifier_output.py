import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "print-verifier-output.py"


class PrintVerifierOutputTests(unittest.TestCase):
    def run_script(self, verifier_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), str(verifier_dir)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_prefers_split_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            verifier_dir = Path(tmp)
            (verifier_dir / "setup-stdout.txt").write_text("installing deps\n")
            (verifier_dir / "suite-stdout.txt").write_text("(fail) example test\n")
            (verifier_dir / "test-stdout.txt").write_text("ignored combined output\n")

            result = self.run_script(verifier_dir)

            self.assertEqual(result.returncode, 0)
            self.assertIn("=== Verifier setup ===", result.stderr)
            self.assertIn("installing deps", result.stderr)
            self.assertIn("=== Verifier suite ===", result.stderr)
            self.assertIn("(fail) example test", result.stderr)
            self.assertNotIn("ignored combined output", result.stderr)

    def test_splits_marker_in_combined_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            verifier_dir = Path(tmp)
            (verifier_dir / "test-stdout.txt").write_text(
                "setup noise\n=== HARBOR_VERIFIER_TESTS ===\n(fail) real test\n"
            )

            result = self.run_script(verifier_dir)

            self.assertEqual(result.returncode, 0)
            self.assertIn("=== Verifier setup ===", result.stderr)
            self.assertIn("setup noise", result.stderr)
            self.assertIn("=== Verifier suite ===", result.stderr)
            self.assertIn("(fail) real test", result.stderr)

    def test_falls_back_to_combined_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            verifier_dir = Path(tmp)
            (verifier_dir / "test-stdout.txt").write_text("only one stream\n")

            result = self.run_script(verifier_dir)

            self.assertEqual(result.returncode, 0)
            self.assertIn("=== Verifier output ===", result.stderr)
            self.assertIn("only one stream", result.stderr)

    def test_hints_prefer_split_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            verifier_dir = Path(tmp)
            (verifier_dir / "setup-stdout.txt").write_text("setup\n")
            (verifier_dir / "suite-stdout.txt").write_text("suite\n")
            (verifier_dir / "test-stdout.txt").write_text("combined\n")

            result = subprocess.run(
                ["python3", str(SCRIPT), str(verifier_dir), "--hints"],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("setup-stdout.txt", result.stdout)
            self.assertIn("suite-stdout.txt", result.stdout)
            self.assertNotIn("test-stdout.txt", result.stdout)

    def test_hints_fall_back_to_combined(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            verifier_dir = Path(tmp)
            (verifier_dir / "test-stdout.txt").write_text("combined\n")

            result = subprocess.run(
                ["python3", str(SCRIPT), str(verifier_dir), "--hints"],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("test-stdout.txt", result.stdout)
            self.assertNotIn("setup-stdout.txt", result.stdout)


if __name__ == "__main__":
    unittest.main()
