import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NEW_TASK = ROOT / "scripts" / "new-task.sh"


class NewTaskScaffoldTests(unittest.TestCase):
    def test_adds_required_submission_records(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        bin_dir = temp_dir / "bin"
        bin_dir.mkdir()
        fake_harbor = bin_dir / "harbor"
        fake_harbor.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
task_name="$3"
mkdir -p "tasks/$task_name/attestations"
printf 'schema_version = "1.3"\\n' > "tasks/$task_name/task.toml"
"""
        )
        fake_harbor.chmod(0o755)
        task_name = "scaffold-test-task"
        task_dir = ROOT / "tasks" / task_name
        try:
            result = subprocess.run(
                ["bash", str(NEW_TASK), task_name],
                capture_output=True,
                text=True,
                check=False,
                cwd=ROOT,
                env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((task_dir / "provenance.json").is_file())
            self.assertTrue(
                (task_dir / "attestations" / "YOUR_GITHUB_HANDLE.md").is_file()
            )
        finally:
            shutil.rmtree(task_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
