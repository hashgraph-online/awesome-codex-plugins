#!/usr/bin/env python3
"""Rank cuts from what judges counted, with code deciding, so no model states a verdict.

  python3 judge_observed.py judge/runs/*.json --key judge/key.json --margin 2

Name each run <CUTID>-<anything>.json, one per fresh call, each a reply to observe-edit-prompt.txt.
Takes the median count per check across runs. A stray picture or a missing point weighs 3, since either
alone can stop a publish; everything else weighs 1. These weights are a starting choice, not a finding,
and they can change the winner, so read the counts as well. Caption fragments count for nothing: on our test
Sonnet found 10-16 and Opus 1-5, so that check does not repeat. A win needs the margin, otherwise it is a tie.
"""
import argparse, glob, itertools, json, os, statistics
from collections import defaultdict

CHECKS = {"points_missing": 3, "stray_pictures": 3, "stumbles_left": 1, "words_stranded": 1, "caption_problems": 1, "visible_jumps": 1, "caption_fragments": 0}


def defects(obs, weights=CHECKS):
    return sum(w * float((obs.get(k) or {}).get("count") or 0) for k, w in weights.items())


def verdict(a, b, margin):
    if abs(a - b) < margin:
        return "tie"
    return "a" if a < b else "b"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("runs", nargs="+"); p.add_argument("--key"); p.add_argument("--margin", type=float, default=2.0); p.add_argument("--json")
    a = p.parse_args()
    key = json.load(open(a.key)) if a.key else {}
    bases = [os.path.basename(v) for v in key.values()]
    name = lambda c: (os.path.basename(key.get(c, c)) if bases.count(os.path.basename(key.get(c, c))) < 2 else "/".join(key[c].split("/")[-2:]))
    runs = defaultdict(list)
    for f in a.runs:
        cid = os.path.basename(f).split("-")[0]
        try:
            runs[cid].append((os.path.basename(f), json.load(open(f))))
        except Exception as e:
            print("skipped %s: %s" % (f, e))
    table = {}
    for c, rs in runs.items():
        med = {k: statistics.median(float((o.get(k) or {}).get("count") or 0) for _, o in rs) for k in CHECKS}
        table[c] = {"counts": med, "defects": round(sum(CHECKS[k] * v for k, v in med.items()), 2), "runs": [round(defects(o), 2) for _, o in rs], "problems": sorted({str(o.get("evidence_problem"))[:100] for _, o in rs if str(o.get("evidence_problem")).lower() not in ("none", "null")})}
    pairs = []
    for x, y in itertools.combinations(sorted(table), 2):
        v = verdict(table[x]["defects"], table[y]["defects"], a.margin)
        pairs.append({"a": name(x), "b": name(y), "a_defects": table[x]["defects"], "b_defects": table[y]["defects"], "winner": name(x) if v == "a" else (name(y) if v == "b" else "too close")})
    rank = sorted(table, key=lambda c: table[c]["defects"])
    res = {"margin": a.margin, "ranking": [{"cut": name(c), **table[c]} for c in rank], "pairs": pairs}
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
