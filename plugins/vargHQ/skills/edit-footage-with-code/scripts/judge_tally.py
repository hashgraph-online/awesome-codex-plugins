#!/usr/bin/env python3
"""Turn judge verdicts into a ranking that admits when it does not know.

  python3 judge_tally.py judge/runs/*.json --key judge/key.json

Each run file is a JSON array of {first_id, second_id, verdict}. A pair run in both orders counts as a win only if
the same cut wins both ways: a flip is a tie. Reports strength by Bradley-Terry (ties count half), the first-slot rate,
and a class for each pair: clear (every vote agrees), leaning (most agree, no flip), too close (the rest).
Without both orders it refuses to call anything clear.
"""
import argparse, json, os
from collections import defaultdict


def load(paths):
    votes = []
    for p in paths:
        for r in json.load(open(p)):
            a, b, v = r.get("first_id"), r.get("second_id"), str(r.get("verdict", "")).lower()
            if a and b and v in ("first", "second", "tie"):
                votes.append({"run": os.path.basename(p), "first": a, "second": b, "verdict": v, "conf": r.get("confidence"), "problem": r.get("evidence_problem")})
    return votes


def bradley_terry(wins, items, rounds=200):
    p = {i: 1.0 for i in items}
    for _ in range(rounds):
        q = {}
        for i in items:
            w = sum(wins[i][j] for j in items if j != i)
            d = sum((wins[i][j] + wins[j][i]) / (p[i] + p[j]) for j in items if j != i)
            q[i] = max(w + 0.01, 0.01) / d if d else p[i]
        s = sum(q.values())
        p = {i: v * len(items) / s for i, v in q.items()}
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+"); ap.add_argument("--key"); ap.add_argument("--json")
    a = ap.parse_args()
    votes = load(a.runs)
    key = json.load(open(a.key)) if a.key else {}
    # several cuts are often called out.mp4: keep the folder when the file name alone is not unique
    bases = [os.path.basename(v) for v in key.values()]
    name = lambda c: (os.path.basename(key.get(c, c)) if bases.count(os.path.basename(key.get(c, c))) < 2
                      else "/".join(key[c].split("/")[-2:]))
    pairs = defaultdict(list)
    for v in votes:
        x, y = sorted((v["first"], v["second"]))
        winner = v["first"] if v["verdict"] == "first" else (v["second"] if v["verdict"] == "second" else None)
        pairs[(x, y)].append({"order": "xy" if v["first"] == x else "yx", "winner": winner})
    first = sum(1 for v in votes if v["verdict"] == "first")
    second = sum(1 for v in votes if v["verdict"] == "second")
    items = sorted({c for p in pairs for c in p})
    wins = {i: {j: 0.0 for j in items} for i in items}
    out = []
    for (x, y), vs in sorted(pairs.items()):
        xy = [v["winner"] for v in vs if v["order"] == "xy"]
        yx = [v["winner"] for v in vs if v["order"] == "yx"]
        cx, cy = sum(1 for v in vs if v["winner"] == x), sum(1 for v in vs if v["winner"] == y)
        ties = len(vs) - cx - cy
        both = bool(xy) and bool(yx)
        lead = x if cx > cy else (y if cy > cx else None)
        flip = both and lead is not None and not (any(w == lead for w in xy) and any(w == lead for w in yx))
        if lead is None or flip or not both:
            cls = "too close" if both else "one order only: not decided"
        elif cx + cy > 0 and min(cx, cy) == 0 and ties == 0:
            cls = "clear"
        else:
            cls = "leaning" if max(cx, cy) >= 2 * (min(cx, cy) + ties) else "too close"
        if cls in ("clear", "leaning"):
            wins[lead][y if lead == x else x] += 1
        else:
            wins[x][y] += 0.5; wins[y][x] += 0.5
        out.append({"a": name(x), "b": name(y), "a_wins": cx, "b_wins": cy, "ties": ties, "class": cls, "winner": name(lead) if cls in ("clear", "leaning") else None})
    bt = bradley_terry(wins, items) if items else {}
    rank = [{"cut": name(c), "strength": round(bt[c], 2)} for c in sorted(items, key=lambda c: -bt[c])]
    decided = first + second
    res = {"votes": len(votes), "first_slot_rate": round(first / decided, 3) if decided else None, "pairs": out, "ranking": rank,
           "evidence_problems": sorted({str(v["problem"])[:120] for v in votes if v["problem"] and str(v["problem"]).lower() not in ("none", "null", "")})[:10]}
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
