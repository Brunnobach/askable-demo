import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-task-metadata.py"
COMMIT = "a" * 40


class ValidateTaskMetadataTests(unittest.TestCase):
    def make_task(
        self,
        *,
        category: str = "Bug Fix",
        languages: list[str] | None = None,
        provenance: dict | None = None,
        attestation_commit: str = COMMIT,
        template_example: bool = False,
        with_attestation: bool = True,
        network_mode: str = "no-network",
        network_justification: str | None = None,
        ai_tools_line: str | None = None,
        dockerfile: str | None = None,
        agent_tooling_justification: str | None = None,
        test_sh: str | None = None,
    ) -> Path:
        task_dir = Path(tempfile.mkdtemp()) / "example-task"
        (task_dir / "attestations").mkdir(parents=True)
        language_values = languages if languages is not None else ["Python"]
        (task_dir / "task.toml").write_text(
            "\n".join(
                [
                    'schema_version = "1.3"',
                    "",
                    "[metadata]",
                    f'category = "{category}"',
                    "primary_languages = ["
                    + ", ".join(f'"{language}"' for language in language_values)
                    + "]",
                    f"template_example = {str(template_example).lower()}",
                ]
                + (
                    [f'network_justification = "{network_justification}"']
                    if network_justification is not None
                    else []
                )
                + (
                    [
                        "agent_tooling_justification = "
                        f'"{agent_tooling_justification}"'
                    ]
                    if agent_tooling_justification is not None
                    else []
                )
                + ([ai_tools_line] if ai_tools_line is not None else [])
                + [
                    "",
                    "[environment]",
                    f'network_mode = "{network_mode}"',
                    "",
                ]
            )
        )
        (task_dir / "provenance.json").write_text(
            json.dumps(
                provenance
                if provenance is not None
                else {
                    "schema_version": 1,
                    "third_party_material": [
                        {
                            "name": "pytest",
                            "source": "https://pypi.org/project/pytest/",
                            "license": "MIT",
                            "version_or_hash": "8.4.1",
                            "ai_training_authorization": "MIT permits this use.",
                        }
                    ],
                }
            )
        )
        if dockerfile is not None:
            (task_dir / "environment").mkdir()
            (task_dir / "environment" / "Dockerfile").write_text(dockerfile)
        if test_sh is not None:
            (task_dir / "tests").mkdir()
            (task_dir / "tests" / "test.sh").write_text(test_sh)
        if with_attestation:
            (task_dir / "attestations" / "jane-doe.md").write_text(
                f"""# Askable Task Contribution Attestation

Task: example-task
Commit: {attestation_commit}
Legal name: Jane Doe
GitHub handle: @janedoe
Date: 2026-07-15

## Declarations

- [x] I hand-wrote the task instruction, or edited it so heavily that every requirement is my own; it was not pasted from an AI tool.
- [x] I personally verified every file in this task — environment, tests, and reference solution — and can explain and defend each decision in a live walkthrough.
- [x] I disclosed every AI tool used on this task in metadata.ai_tools_used in task.toml.
- [x] I own or have authority to contribute all material in my contribution.
- [x] I assign all right, title, and interest in my contribution to Askable.

Signature: Jane Doe
"""
            )
        return task_dir

    def validate(
        self, task_dir: Path, commit: str = COMMIT
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--task",
                str(task_dir),
                "--commit",
                commit,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_accepts_complete_task_metadata(self) -> None:
        result = self.validate(self.make_task())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_unknown_category(self) -> None:
        result = self.validate(self.make_task(category="Documentation"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("category", result.stderr)

    def test_rejects_empty_primary_languages(self) -> None:
        result = self.validate(self.make_task(languages=[]))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("primary_languages", result.stderr)

    def test_rejects_incomplete_provenance_record(self) -> None:
        result = self.validate(
            self.make_task(
                provenance={
                    "schema_version": 1,
                    "third_party_material": [{"name": "pytest"}],
                }
            )
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("provenance", result.stderr)

    def test_rejects_attestation_for_a_different_commit(self) -> None:
        result = self.validate(self.make_task(attestation_commit="b" * 40))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("attestation", result.stderr)

    def test_accepts_template_example_without_contributor_attestation(self) -> None:
        result = self.validate(
            self.make_task(template_example=True, with_attestation=False)
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_network_access_without_justification(self) -> None:
        result = self.validate(self.make_task(network_mode="public"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("network_mode", result.stderr)

    def test_accepts_network_access_with_justification(self) -> None:
        result = self.validate(
            self.make_task(
                network_mode="public",
                network_justification="Task teaches the agent to debug a live DNS resolver.",
            )
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_accepts_a_disclosed_ai_tool_list(self) -> None:
        result = self.validate(
            self.make_task(ai_tools_line='ai_tools_used = ["claude-code"]')
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_ai_tools_used_that_is_not_a_list(self) -> None:
        result = self.validate(
            self.make_task(ai_tools_line='ai_tools_used = "claude-code"')
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ai_tools_used", result.stderr)

    def test_rejects_a_dockerfile_without_git(self) -> None:
        result = self.validate(
            self.make_task(
                dockerfile="FROM ubuntu:24.04\nRUN apt-get install -y tmux\nWORKDIR /app\n"
            )
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git", result.stderr)

    def test_accepts_a_dockerfile_with_a_git_baseline(self) -> None:
        result = self.validate(
            self.make_task(
                dockerfile=(
                    "FROM ubuntu:24.04\n"
                    "RUN apt-get install -y tmux asciinema\n"
                    "RUN git init && git commit -m base --allow-empty\n"
                )
            )
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_a_dockerfile_without_tmux(self) -> None:
        # terminus-2 cannot start a session without tmux, and an offline runtime
        # cannot install it, so every calibration attempt would error out before
        # the agent read the instruction.
        result = self.validate(
            self.make_task(
                dockerfile=(
                    "FROM ubuntu:24.04\n"
                    "RUN git init && git commit -m base --allow-empty\n"
                )
            )
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tmux", result.stderr)

    def test_accepts_a_dockerfile_without_tmux_when_justified(self) -> None:
        result = self.validate(
            self.make_task(
                dockerfile=(
                    "FROM ghcr.io/example/base-with-tmux:1\n"
                    "RUN git init && git commit -m base --allow-empty\n"
                ),
                agent_tooling_justification="The base image already ships tmux.",
            )
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_a_verifier_that_runs_pytest_on_the_agents_sys_path(self) -> None:
        # The verifier starts in the agent's WORKDIR (/app), and `python -m`
        # puts that cwd first on sys.path — a planted /app/json.py shadows the
        # stdlib inside the suite and can forge the reward.
        result = self.validate(
            self.make_task(
                test_sh="#!/bin/bash\npython3 -m pytest /tests/test_outputs.py\n"
            )
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sys.path", result.stderr)

    def test_accepts_the_hardened_pytest_invocation(self) -> None:
        result = self.validate(
            self.make_task(
                test_sh=(
                    "#!/bin/bash\n"
                    "cd /tests && python3 -P -m pytest -p no:cacheprovider "
                    "test_outputs.py\n"
                )
            )
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_accepts_a_verifier_that_does_not_use_the_python_launcher(self) -> None:
        # Only the `python -m pytest` launcher form is rejected; other runners
        # (and a bare pytest entry point) are the author's judgement call.
        result = self.validate(
            self.make_task(test_sh="#!/bin/bash\ncd /tests && bun test test_outputs.ts\n")
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_accepts_an_uncalibrated_task_with_a_sha_bound_attestation(self) -> None:
        result = self.validate(self.make_task(), commit="UNCALIBRATED")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_an_uncalibrated_task_with_a_malformed_attestation_commit(self) -> None:
        result = self.validate(
            self.make_task(attestation_commit="not-a-sha"), commit="UNCALIBRATED"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("40-character", result.stderr)

    def test_rejects_a_missing_environment_section(self) -> None:
        task_dir = self.make_task()
        task_toml = task_dir / "task.toml"
        content = task_toml.read_text()
        content = content.split("[environment]")[0]
        task_toml.write_text(content)
        result = self.validate(task_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("network_mode", result.stderr)

    def test_rejects_a_task_whose_files_are_gitignored(self) -> None:
        # A rule matching inside tasks/ drops files from the commit while
        # leaving them on the author's disk: green locally, incomplete on
        # arrival. This is how a run.log corpus was lost.
        task_dir = self.make_task()
        repo = task_dir.parent
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        (repo / ".gitignore").write_text("*.log\n")
        (task_dir / "fixtures").mkdir(parents=True, exist_ok=True)
        (task_dir / "fixtures" / "run.log").write_text("exit 0\n")
        result = self.validate(task_dir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("gitignore", result.stderr)

    def test_accepts_a_task_with_no_ignored_files(self) -> None:
        task_dir = self.make_task()
        repo = task_dir.parent
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        (repo / ".gitignore").write_text("/*.log\n")
        (task_dir / "fixtures").mkdir(parents=True, exist_ok=True)
        (task_dir / "fixtures" / "run.log").write_text("exit 0\n")
        result = self.validate(task_dir)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
