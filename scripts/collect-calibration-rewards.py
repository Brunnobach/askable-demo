#!/usr/bin/env python3
"""Collect new Harbor verifier rewards produced by a calibration run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def reward_paths(jobs_dir: Path) -> dict[str, Path]:
    candidates: dict[str, Path] = {}
    for path in jobs_dir.rglob("reward.txt"):
        candidates[str(path.parent.relative_to(jobs_dir))] = path
    for path in jobs_dir.rglob("reward.json"):
        candidates[str(path.parent.relative_to(jobs_dir))] = path
    return candidates


def read_reward(path: Path) -> int:
    if path.suffix == ".json":
        value = json.loads(path.read_text()).get("reward")
    else:
        value = path.read_text().strip()
    if value in (1, 1.0, "1", "1.0"):
        return 1
    if value in (0, 0.0, "0", "0.0"):
        return 0
    raise ValueError(f"{path} contains a non-binary reward")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs-dir", type=Path, required=True)
    parser.add_argument("--snapshot-out", type=Path)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected", type=int, default=8)
    args = parser.parse_args()

    if bool(args.snapshot_out) == bool(args.snapshot):
        parser.error("provide exactly one of --snapshot-out or --snapshot")
    if args.snapshot and not args.output:
        parser.error("--output is required with --snapshot")

    paths = reward_paths(args.jobs_dir)
    if args.snapshot_out:
        args.snapshot_out.write_text(
            json.dumps({"paths": sorted(paths)}, indent=2) + "\n"
        )
        return 0

    try:
        before = set(json.loads(args.snapshot.read_text())["paths"])
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"Error: invalid reward snapshot: {error}", file=sys.stderr)
        return 1

    new_paths = sorted(set(paths) - before)
    try:
        rewards = [read_reward(paths[path]) for path in new_paths]
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if len(rewards) != args.expected:
        print(
            f"Error: expected {args.expected} new verifier rewards, found {len(rewards)}",
            file=sys.stderr,
        )
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"rewards": rewards}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
