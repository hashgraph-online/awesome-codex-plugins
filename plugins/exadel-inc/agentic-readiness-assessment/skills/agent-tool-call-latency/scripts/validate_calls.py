#!/usr/bin/env python3
"""Check calls.jsonl against references/SCHEMA.md and print what to spot-check by hand.

    validate_calls.py calls.jsonl [--harness NAME] [--samples 3]

Exits 1 on a schema error. Warnings flag shapes that usually mean a pairing or clock bug in an
adapter: many zero-length calls, calls longer than a day, or shell calls without a command.
"""
import argparse
import collections
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import KINDS, OPTIONAL, REQUIRED, TIMINGS  # noqa: E402

DAY_MS = 86_400_000


def check(rec):
    errors = []
    for key, typ in REQUIRED.items():
        if key not in rec:
            errors.append(f"missing {key}")
        elif not isinstance(rec[key], typ) or isinstance(rec[key], bool):
            errors.append(f"{key} has type {type(rec[key]).__name__}")
    for key, typ in OPTIONAL.items():
        if key in rec and not isinstance(rec[key], typ):
            errors.append(f"{key} has type {type(rec[key]).__name__}")
    unknown = set(rec) - set(REQUIRED) - set(OPTIONAL)
    if unknown:
        errors.append(f"unknown fields {sorted(unknown)}")
    if rec.get("kind") not in KINDS:
        errors.append(f"kind {rec.get('kind')!r} not in {sorted(KINDS)}")
    if "timing" in rec and rec["timing"] not in TIMINGS:
        errors.append(f"timing {rec['timing']!r} not in {sorted(TIMINGS)}")
    if isinstance(rec.get("dur_ms"), (int, float)) and rec["dur_ms"] < 0:
        errors.append("negative dur_ms")
    if isinstance(rec.get("ts"), (int, float)) and not 1e12 <= rec["ts"] <= 1e13:
        errors.append("ts is not epoch milliseconds")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("calls")
    ap.add_argument("--harness", help="only this harness (for a new adapter)")
    ap.add_argument("--samples", type=int, default=3, help="random calls per harness to spot-check")
    args = ap.parse_args()

    recs, bad, keys = [], 0, collections.Counter()
    with open(args.calls) as fh:
        for n, line in enumerate(fh, 1):
            try:
                rec = json.loads(line)
            except ValueError:
                print(f"line {n}: not JSON")
                bad += 1
                continue
            if args.harness and rec.get("harness") != args.harness:
                continue
            errors = check(rec)
            if errors:
                bad += 1
                if bad <= 20:
                    print(f"line {n}: {'; '.join(errors)}")
                continue
            keys[(rec["agent"], rec["id"])] += 1
            recs.append(rec)
    dupes = sum(v - 1 for v in keys.values() if v > 1)

    by_harness = collections.defaultdict(list)
    for r in recs:
        by_harness[r["harness"]].append(r)
    print(f"{len(recs)} valid calls, {bad} invalid, {dupes} duplicate (agent, id)")
    rng = random.Random(0)
    for harness, rs in sorted(by_harness.items(), key=lambda kv: -len(kv[1])):
        n = len(rs)
        zero = sum(r["dur_ms"] == 0 for r in rs) / n
        huge = sum(r["dur_ms"] > DAY_MS for r in rs)
        shell = [r for r in rs if r["kind"] == "shell"]
        no_cmd = sum(not r.get("command") for r in shell)
        timing = collections.Counter(r.get("timing", "unset") for r in rs)
        kinds = collections.Counter(r["kind"] for r in rs)
        print(f"\n{harness}: {n} calls, kinds {dict(kinds.most_common())}, timing {dict(timing)}")
        if zero > 0.2:
            print(f"  WARN {zero:.0%} of calls last 0 ms: start and end probably come from the same line")
        if huge:
            print(f"  WARN {huge} calls last over a day: a result was probably paired with the wrong call")
        if shell and no_cmd / len(shell) > 0.05:
            print(f"  WARN {no_cmd} of {len(shell)} shell calls have no command, so they cannot be classified")
        if kinds.get("other", 0) / n > 0.3:
            print(f"  WARN {kinds['other'] / n:.0%} of calls have kind 'other': map the harness's tool names")
        for r in rng.sample(rs, min(args.samples, n)):
            what = r.get("command") or r.get("mcp_tool") or r.get("detail") or ""
            print(f"  check {r.get('src', '(no src)')}  {r['tool']}  {r['dur_ms'] / 1000:.2f}s  {what[:80]}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
