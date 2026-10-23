#!/usr/bin/env python3
"""Print verifier logs with setup vs test sections when available."""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = "=== HARBOR_VERIFIER_TESTS ==="


def _print_section(label: str, content: str) -> None:
    if not content.strip():
        return
    print(f"\n=== {label} ===", file=sys.stderr)
    print(content.rstrip("\n"), file=sys.stderr)


def print_verifier_output(verifier_dir: Path) -> int:
    setup = verifier_dir / "setup-stdout.txt"
    suite = verifier_dir / "suite-stdout.txt"
    # Harbor always captures the whole test.sh run here.
    combined = verifier_dir / "test-stdout.txt"

    if setup.exists() or suite.exists():
        if setup.exists():
            _print_section("Verifier setup", setup.read_text())
        if suite.exists():
            _print_section("Verifier suite", suite.read_text())
        return 0

    if not combined.exists():
        print(f"No verifier output found in {verifier_dir}", file=sys.stderr)
        return 1

    text = combined.read_text()
    marker_line = f"{MARKER}\n"
    if marker_line in text:
        setup_text, suite_text = text.split(marker_line, 1)
        _print_section("Verifier setup", setup_text)
        _print_section("Verifier suite", suite_text)
        return 0

    _print_section("Verifier output", text)
    return 0


def raw_file_hints(verifier_dir: Path) -> list[str]:
    """Return cat commands for the most useful existing verifier log files."""
    setup = verifier_dir / "setup-stdout.txt"
    suite = verifier_dir / "suite-stdout.txt"
    combined = verifier_dir / "test-stdout.txt"
    hints: list[str] = []

    if setup.exists() or suite.exists():
        if setup.exists():
            hints.append(f"cat {setup}")
        if suite.exists():
            hints.append(f"cat {suite}")
    elif combined.exists():
        hints.append(f"cat {combined}")

    return hints


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <verifier-dir> [--hints]", file=sys.stderr)
        return 2

    verifier_dir = Path(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == "--hints":
        for hint in raw_file_hints(verifier_dir):
            print(f"  {hint}")
        return 0

    return print_verifier_output(verifier_dir)


if __name__ == "__main__":
    raise SystemExit(main())
