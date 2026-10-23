import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "scripts" / "export-task.sh"


class ExportTaskTests(unittest.TestCase):
    def test_exports_the_template_example_with_a_manifest(self) -> None:
        out_dir = Path(tempfile.mkdtemp())
        result = subprocess.run(
            ["bash", str(EXPORT), "tasks/hello-world-py", "--out", str(out_dir)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        archives = list(out_dir.glob("hello-world-py-*.tar.gz"))
        self.assertEqual(len(archives), 1, result.stdout)
        with tarfile.open(archives[0]) as archive:
            names = archive.getnames()
            self.assertIn("hello-world-py/task.toml", names)
            self.assertIn("hello-world-py/manifest.json", names)
            manifest_member = archive.extractfile("hello-world-py/manifest.json")
            assert manifest_member is not None
            manifest = json.loads(manifest_member.read().decode())
        self.assertEqual(manifest["task"], "hello-world-py")
        manifest_paths = {entry["path"] for entry in manifest["files"]}
        self.assertIn("task.toml", manifest_paths)

    def test_rejects_a_directory_without_task_toml(self) -> None:
        empty_dir = Path(tempfile.mkdtemp())
        result = subprocess.run(
            ["bash", str(EXPORT), str(empty_dir)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task.toml", result.stderr)


if __name__ == "__main__":
    unittest.main()
