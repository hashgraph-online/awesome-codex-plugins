#!/usr/bin/env python3
"""Measure how far two AI judges (or a judge and a person) agree, before trusting either.

  python3 judge_agreement.py judge_a.json judge_b.json [--human human.json]

Each file is a JSON object {item_id: {criterion: "yes" | "no" | "na", ...}, ...}, the output format of the judge
prompt in references/judge.md. Reports raw agreement, Cohen's kappa, per-criterion agreement and, with --human,
each judge's true-positive and true-negative rate against the person (the numbers to quote for a calibrated judge).
Rule of thumb: kappa below ~0.6 on a criterion means the criterion is not clear enough yet; rewrite it.
"""
import argparse, json
from collections import Counter

LABELS = ("yes", "no", "na")

def norm(v):
    v = str(v).strip().lower()
    return "yes" if v.startswith(("yes", "pass", "true")) else "no" if v.startswith(("no", "fail", "false")) else "na"

def load(path):
    data = json.load(open(path))
    return {i: {c: norm(v) for c, v in crit.items()} for i, crit in data.items() if isinstance(crit, dict)}

def kappa(pairs):
    n = len(pairs)
    if not n:
        return float("nan"), float("nan")
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[l] * cb[l] for l in LABELS) / (n * n)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0

def pairs_of(a, b):
    out = {}
    for item in set(a) & set(b):
        for crit in set(a[item]) & set(b[item]):
            out.setdefault(crit, []).append((a[item][crit], b[item][crit]))
    return out

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("judge_a"); ap.add_argument("judge_b"); ap.add_argument("--human")
args = ap.parse_args()
A, B = load(args.judge_a), load(args.judge_b)
per = pairs_of(A, B)
allp = [p for v in per.values() for p in v]
po, k = kappa(allp)
print(f"judge vs judge: {len(allp)} calls, agreement {po:.2f}, kappa {k:.2f}")
for crit, ps in sorted(per.items(), key=lambda kv: kappa(kv[1])[1]):
    po_c, k_c = kappa(ps)
    flag = "  <- rewrite this criterion" if k_c < 0.6 else ""
    print(f"  {crit:32s} n={len(ps):3d} agree {po_c:.2f} kappa {k_c:.2f}{flag}")
if args.human:
    H = load(args.human)
    for name, J in (("judge_a", A), ("judge_b", B)):
        tp = fn = tn = fp = 0
        for item in set(H) & set(J):
            for crit, h in H[item].items():
                j = J[item].get(crit)
                if h == "na" or j is None or j == "na":
                    continue
                if h == "yes":
                    tp += j == "yes"; fn += j == "no"
                else:
                    tn += j == "no"; fp += j == "yes"
        tpr = tp / (tp + fn) if tp + fn else float("nan")
        tnr = tn / (tn + fp) if tn + fp else float("nan")
        print(f"{name} vs human: TPR {tpr:.2f} (passes it finds), TNR {tnr:.2f} (fails it catches)")
