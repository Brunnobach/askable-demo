#!/usr/bin/env python3
"""Create a reproducible calibration record from verifier rewards.

The agent, model, attempt count, and eligibility band come from a
calibration target file (default: calibration-target.json at the repo
root), so an engagement can swap the designated model and band without
editing this script.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = ROOT / "calibration-target.json"
TARGET_FIELDS = ("agent", "model", "attempt_count", "min_success", "max_success")


def load_target(path: Path) -> dict:
    try:
        target = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read calibration target: {error}") from error

    for field in TARGET_FIELDS:
        if field not in target:
            raise ValueError(f"calibration target is missing '{field}'")
    attempts = target["attempt_count"]
    low, high = target["min_success"], target["max_success"]
    if not (isinstance(attempts, int) and attempts > 0):
        raise ValueError("attempt_count must be a positive integer")
    if not (
        isinstance(low, int)
        and isinstance(high, int)
        and 0 <= low <= high <= attempts
    ):
        raise ValueError(
            "eligibility band must satisfy 0 <= min_success <= max_success <= attempt_count"
        )
    return target


def load_rewards(path: Path, attempt_count: int) -> list[int]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read rewards file: {error}") from error

    rewards = payload.get("rewards") if isinstance(payload, dict) else None
    if not isinstance(rewards, list) or len(rewards) != attempt_count:
        raise ValueError(f"expected exactly {attempt_count} rewards")
    if any(reward not in (0, 1) for reward in rewards):
        raise ValueError("rewards must be binary 0 or 1 values")
    return rewards


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--rewards-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="record an author self-check rather than the authoritative run: "
        "the record is marked non-authoritative and a band miss is reported "
        "without failing, because a self-check is information, not a verdict",
    )
    args = parser.parse_args()

    try:
        target = load_target(args.target)
        rewards = load_rewards(args.rewards_file, target["attempt_count"])
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    attempt_count = target["attempt_count"]
    success_count = sum(rewards)
    pass_rate = success_count / attempt_count
    accepted = target["min_success"] <= success_count <= target["max_success"]
    record = {
        "schema_version": 2,
        "task": args.task,
        "commit": args.commit,
        "agent": target["agent"],
        "model": target["model"],
        "attempt_count": attempt_count,
        "min_success": target["min_success"],
        "max_success": target["max_success"],
        "rewards": rewards,
        "success_count": success_count,
        "pass_rate": pass_rate,
        "accepted": accepted,
        "authoritative": not args.self_check,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n")

    if not accepted:
        band = (
            f"{target['min_success']}–{target['max_success']} successful trials "
            f"out of {attempt_count}"
        )
        if args.self_check:
            # A self-check is a signal to act on before submitting, not a verdict.
            print(
                f"Self-check outside the band ({success_count}/{attempt_count}; "
                f"eligible is {band}). Deepen the problem — do not hide "
                "requirements (AUTHORING.md §8).",
                file=sys.stderr,
            )
            return 0
        print(f"Error: calibration requires {band}", file=sys.stderr)
        return 1

    print(
        f"Accepted: {success_count}/{attempt_count} successes "
        f"(pass rate {pass_rate:.3f})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
