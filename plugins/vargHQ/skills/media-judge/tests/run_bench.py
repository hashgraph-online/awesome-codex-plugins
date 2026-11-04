#!/usr/bin/env python3
"""Run the judge on every fixture, then report catches, misses and false flags against truth.json.

  python3 run_bench.py fixtures/ runs/ [--only name] [--jobs 4]"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

JUDGE = Path(__file__).resolve().parent.parent / "scripts" / "judge.py"
sys.path.insert(0, str(JUDGE.parent))
# Read the table from the source, so this script needs nothing but the standard library.
_table = re.search(r"SEVERITY = \{(.*?)\n\}", (JUDGE.parent / "mj_rank.py").read_text(), re.S).group(1)
SEVERITY = dict(re.findall(r'"(\w+)": "(\w+)"', _table))


def one(name: str, spec: dict, fixtures: Path, runs: Path, fresh: bool) -> tuple[str, dict | None, str]:
    out = runs / name
    facts = out / "facts.json"
    if fresh or not facts.exists():
        cmd = ["uv", "run", "--quiet", "--script", str(JUDGE), "video", str(fixtures / f"{name}.mp4"), "--out", str(out), "--music-only", *[x.replace("{fixtures}", str(fixtures)) for x in spec.get("args", [])]]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode not in (0, 1):
            return name, None, p.stderr[-800:]
    return name, json.loads(facts.read_text()), ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fixtures")
    ap.add_argument("runs")
    ap.add_argument("--only")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--fresh", action="store_true")
    a = ap.parse_args()
    fx, runs = Path(a.fixtures), Path(a.runs)
    truth = json.loads((fx / "truth.json").read_text())
    names = [n for n in truth if not a.only or a.only in n]
    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(lambda n: one(n, truth[n], fx, runs, a.fresh), names))
    caught, missed, late, false_flags, controls_clean, controls = 0, [], [], [], 0, 0
    notes = 0
    rows = []
    # The base footage is real, so it has real findings. Those are named once and not counted as false flags.
    base = next((f for n, f, _ in results if n == "control_clean" and f), None)
    baseline = {c["check"] for c in base["checks"] if c["state"] == "flagged"} if base else set()
    if baseline:
        print(f"Findings in the unaltered base footage: {', '.join(sorted(baseline))}\n")
    for name, facts, err in results:
        if facts is None:
            rows.append((name, "CRASH", err[-200:]))
            missed.append(name)
            continue
        all_flagged = {c["check"]: c for c in facts["checks"] if c["state"] == "flagged"}
        spec = truth[name]
        flagged = {k: v for k, v in all_flagged.items() if k not in baseline or k in spec["expect"]}
        if name.startswith("control"):
            controls += 1
            flagged.update({k: all_flagged[k] for k in spec.get("must_clear", []) if k in all_flagged})
            hard = sorted(k for k in flagged if SEVERITY.get(k, "minor") != "minor" or k in spec.get("must_clear", []))
            soft = sorted(k for k in flagged if k not in hard)
            notes += len(soft)
            if hard:
                false_flags.append((name, hard))
                rows.append((name, "FALSE FLAG", ", ".join(hard) + (f"  minor: {', '.join(soft)}" if soft else "")))
            else:
                controls_clean += 1
                rows.append((name, "clean", f"minor: {', '.join(soft)}" if soft else ""))
            continue
        want = spec["expect"]
        hit = []
        for w in want:
            c = flagged.get(w)
            if not c:
                continue
            times = [e["t"] for e in c["events"] if isinstance(e, dict) and isinstance(e.get("t"), (int, float))]
            ends = [e.get("t_end", e["t"]) for e in c["events"] if isinstance(e, dict) and isinstance(e.get("t"), (int, float))]
            at = spec.get("at")
            # An event has to land on the planted moment, not just anywhere.
            if at is None or not times or any(a - 1.0 <= at <= b + 1.0 for a, b in zip(times, ends)):
                hit.append(w)
        extra = sorted(set(flagged) - set(want))
        if hit:
            caught += 1
            rows.append((name, "caught", f"{', '.join(hit)}" + (f"  also: {', '.join(extra)}" if extra else "")))
        else:
            missed.append(name)
            rows.append((name, "MISSED", f"wanted {want}; flagged {sorted(flagged)}"))
    w = max(len(r[0]) for r in rows)
    for r in rows:
        print(f"{r[0]:<{w}}  {r[1]:<11} {r[2]}")
    print(f"\nDefects caught: {caught} of {caught + len(missed)}. Controls with no blocker or major flag: {controls_clean} of {controls}. Minor notes on controls: {notes}.")
    (runs / "bench.json").write_text(json.dumps({"caught": caught, "missed": missed, "controls_clean": controls_clean, "controls": controls, "notes_on_controls": notes, "baseline": sorted(baseline), "rows": rows}, indent=1))


if __name__ == "__main__":
    main()
