"""The shipped verifiers must not trust the directory the agent controls.

Harbor starts tests/test.sh in the image WORKDIR (/app in every template
task) — the directory the agent has been writing to all episode. The
`python3 -m` launcher puts that cwd first on sys.path, so an agent that left
a /app/pathlib.py (or json.py, csv.py, ...) behind would have its module
imported by the suite in place of the stdlib and could forge a passing run.
bun has the same class of problem: it loads bunfig.toml — including
[test].preload, which executes arbitrary scripts inside the test process —
from its cwd. These tests pin every shipped test.sh to the hardened
invocation, because the hello-world examples are the lines every author
copies.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_SCRIPTS = sorted(ROOT.glob("tasks/*/tests/test.sh"))

# The python launcher followed by its own options, up to `-m pytest`, without
# crossing a shell command boundary.
PYTEST_LAUNCH = re.compile(r"\bpython[0-9.]*\s+(?P<opts>[^|&;]*?)-m\s+pytest\b")


def command_lines(script: Path) -> list[tuple[int, str]]:
    """Return (line number, code) pairs with comments stripped."""
    lines = []
    for number, line in enumerate(script.read_text().splitlines(), start=1):
        code = line.split("#", 1)[0].strip()
        if code:
            lines.append((number, code))
    return lines


class VerifierInvocationTests(unittest.TestCase):
    def test_the_template_ships_task_test_scripts(self) -> None:
        # Guard the glob: if the task layout moves, the other tests here would
        # pass vacuously while checking nothing.
        self.assertTrue(TEST_SCRIPTS, f"no tasks/*/tests/test.sh found under {ROOT}")

    def test_pytest_never_runs_with_the_agents_cwd_on_sys_path(self) -> None:
        for script in TEST_SCRIPTS:
            for number, code in command_lines(script):
                match = PYTEST_LAUNCH.search(code)
                if not match:
                    continue
                self.assertRegex(
                    match.group("opts"),
                    r"(^|\s)-P(\s|$)",
                    f"{script}:{number} runs `python -m pytest` without -P, so "
                    "the agent's WORKDIR is first on sys.path and a planted "
                    "/app/json.py shadows the stdlib inside the verifier",
                )

    def test_pytest_plugin_flags_come_after_the_pytest_module(self) -> None:
        # `-p no:cacheprovider` is a pytest flag; placed before `-m pytest` it
        # is parsed by Python itself, which dies with "Unknown option: -p".
        # test.sh derives the reward from $?, so that launcher error silently
        # scores every trial 0 — the oracle included.
        for script in TEST_SCRIPTS:
            for number, code in command_lines(script):
                match = PYTEST_LAUNCH.search(code)
                if not match:
                    continue
                self.assertNotRegex(
                    match.group("opts"),
                    r"(^|\s)-p(\s|$)",
                    f"{script}:{number} passes -p to the Python launcher; it "
                    "must come after `-m pytest` or every trial scores 0",
                )

    def test_the_suite_runs_from_tests_not_from_the_agents_workdir(self) -> None:
        # Belt and braces for pytest (no cwd artifacts like .pytest_cache),
        # load-bearing for bun (bunfig.toml is read from the cwd).
        for script in TEST_SCRIPTS:
            for number, code in command_lines(script):
                runner = re.search(r"\bpython[0-9.]*\s[^|&;]*-m\s+pytest\b|\bbun test\b", code)
                if not runner:
                    continue
                prefix = code[: runner.start()]
                self.assertRegex(
                    prefix,
                    r"\bcd /tests\b",
                    f"{script}:{number} runs the suite from the agent's cwd; "
                    "prefix it with `cd /tests && `",
                )

    def test_bun_is_given_a_path_not_a_bare_filter(self) -> None:
        # `bun test <name>` treats a bare argument as a *filter*, not a path,
        # and bun only discovers files carrying ".test"/".spec" in the name.
        # So `bun test test_outputs.ts` from /tests matches nothing, reports
        # "filters did not match any test files", exits non-zero and scores
        # the trial 0 while looking like an ordinary test failure. An absolute
        # path or a leading ./ is read as a path instead. This shipped once.
        for script in TEST_SCRIPTS:
            for number, code in command_lines(script):
                match = re.search(r"\bbun\s+test\s+(?P<args>[^|&;<>]*)", code)
                if not match:
                    continue
                paths = [a for a in match.group("args").split() if not a.startswith("-")]
                for arg in paths:
                    self.assertRegex(
                        arg,
                        r"^(/|\./|\.\./)",
                        f"{script}:{number} passes `{arg}` to bun test as a bare "
                        "filter; bun will discover no files and score the trial 0. "
                        "Use ./ or an absolute path.",
                    )


if __name__ == "__main__":
    unittest.main()
