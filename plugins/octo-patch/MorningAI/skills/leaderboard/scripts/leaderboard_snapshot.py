#!/usr/bin/env python3
"""CLI for leaderboard snapshot management.

Usage:
    # Save snapshot and print diff against previous
    python3 skills/leaderboard/scripts/leaderboard_snapshot.py save \\
        --leaderboard lmsys --date 2026-04-14 \\
        --data '[{"model":"GPT-4o","rank":1,"score":1287}]'

    # Show the latest saved snapshot
    python3 skills/leaderboard/scripts/leaderboard_snapshot.py latest --leaderboard lmsys
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from lib.snapshots import diff_snapshot, get_latest_snapshot, save_snapshot


def cmd_save(args):
    entries = json.loads(args.data)
    save_snapshot(args.leaderboard, args.date, entries)
    result = diff_snapshot(args.leaderboard, args.date)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_latest(args):
    result = get_latest_snapshot(args.leaderboard)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Leaderboard snapshot tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p_save = sub.add_parser("save", help="Save snapshot and show diff")
    p_save.add_argument("--leaderboard", required=True)
    p_save.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_save.add_argument("--data", required=True, help="JSON array of model entries")
    p_save.set_defaults(func=cmd_save)

    p_latest = sub.add_parser("latest", help="Show latest snapshot")
    p_latest.add_argument("--leaderboard", required=True)
    p_latest.set_defaults(func=cmd_latest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
