#!/usr/bin/env python3
"""Run a blind LLM judging round. Standard library only. Read references/judging.md first.

  python3 judge_pack.py pack take1.jpg take2.jpg take3.jpg --brief brief.txt --purpose "A guide clip for a video model" --out round1/ \\
      --criteria "the woman is at the window in the last shot; nothing covers a head; flat light with no drama, since the video model must not copy it"
      Copies each item to a random name, adds a duplicate as a sanity check, and writes round1/jobs.json: one job per pair per order,
      each with its prompt. Keeps the name map in round1/key.json. Don't show that file to a judge.
      Run every job in a FRESH context with no other history. Save each reply as {"id": ..., "winner": "A"|"B"|"tie", "judge": "model name"}, one JSON per line.

  python3 judge_pack.py score round1/ replies.jsonl
      Both orders must agree or the pair counts as a tie. Prints wins, ties, tiers, the sanity check and where judges disagree.
"""
import argparse
import itertools
import json
import random
import shutil
import uuid
from collections import defaultdict
from pathlib import Path

PAIR = """BRIEF: {brief}

PURPOSE: {purpose}

Two pictures, A and B. Look at both before you decide.
A: {a}
B: {b}

Compare them on these points, one at a time, in this order: {criteria}.
For each point, write what you see in A and what you see in B, and cite where. Don't reward polish, colour, lighting or detail unless a point asks about it.
Only then decide which serves the purpose better. If neither does, say tie: ties are a normal answer.
Reply with only JSON: {{"notes": {{"point": "..."}}, "winner": "A"}} where winner is A, B or tie."""


def pack(a):
    out = Path(a.out)
    (out / "items").mkdir(parents=True, exist_ok=True)
    rng = random.Random(a.seed)
    key = {}
    items = []
    for src in a.items:
        src = Path(src)
        name = uuid.UUID(int=rng.getrandbits(128)).hex[:8] + src.suffix.lower()
        shutil.copy(src, out / "items" / name)
        key[name] = src.name
        items.append(name)
    # the sanity pair: one item against an exact copy of itself. It has to come back a tie.
    dup = uuid.UUID(int=rng.getrandbits(128)).hex[:8] + Path(items[0]).suffix
    shutil.copy(out / "items" / items[0], out / "items" / dup)
    key[dup] = key[items[0]] + " (copy)"
    criteria = [c.strip() for c in a.criteria.split(";") if c.strip()]
    brief = Path(a.brief).read_text().strip()
    jobs = []
    for x, y in list(itertools.combinations(items, 2)) + [(items[0], dup)]:
        for first, second in ((x, y), (y, x)):
            order = criteria[:]
            rng.shuffle(order)     # later criteria drift towards earlier scores, so vary the order
            jobs.append(dict(id=uuid.UUID(int=rng.getrandbits(128)).hex[:10], a=first, b=second,
                             prompt=PAIR.format(brief=brief, purpose=a.purpose, a=(out / "items" / first).resolve(), b=(out / "items" / second).resolve(), criteria="; ".join(order))))
    rng.shuffle(jobs)
    (out / "jobs.json").write_text(json.dumps(jobs, indent=1))
    (out / "key.json").write_text(json.dumps(dict(names=key, sanity=[items[0], dup]), indent=1))
    print(f"{len(items)} items, {len(jobs)} jobs in {out}/jobs.json. Run each in a fresh context, ideally through two model families.")


def score(a):
    out = Path(a.dir)
    jobs = {j["id"]: j for j in json.loads((out / "jobs.json").read_text())}
    key = json.loads((out / "key.json").read_text())
    names = key["names"]
    verdicts = defaultdict(lambda: defaultdict(list))
    for line in Path(a.replies).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        j = jobs[r["id"]]
        w = str(r.get("winner", "tie")).strip().lower()
        picked = j["a"] if w == "a" else j["b"] if w == "b" else None
        verdicts[frozenset((j["a"], j["b"]))][r.get("judge", "judge")].append(picked)
    wins = defaultdict(float)
    played = defaultdict(int)
    split = []
    sanity = frozenset(key["sanity"])
    ok = True
    for pair, by_judge in verdicts.items():
        results = {}
        for judge, picks in by_judge.items():
            # both orders must name the same item, otherwise it's a tie
            results[judge] = picks[0] if len(picks) >= 2 and all(p == picks[0] for p in picks) and picks[0] else None
        if pair == sanity:
            ok = all(v is None for v in results.values())
            print("SANITY identical pair:", "tie, good" if ok else f"NOT a tie: {results}. Don't trust this round: the judge is picking by position or habit.")
            continue
        vals = set(results.values())
        a_, b_ = tuple(pair)
        played[a_] += 1
        played[b_] += 1
        if len(vals) == 1 and None not in vals:
            wins[vals.pop()] += 1
        else:
            wins[a_] += .5
            wins[b_] += .5
            if len(vals) > 1:
                split.append((names[a_], names[b_], {k: names.get(v, "tie") for k, v in results.items()}))
    table = sorted(played, key=lambda k: -wins[k] / max(played[k], 1))
    print("\nitem                            wins / pairs")
    for k in table:
        print(f"{names[k]:32s}{wins[k]:4.1f} / {played[k]}")
    if table:
        top = wins[table[0]]
        print("\nTop tier (send these to a person):", ", ".join(names[k] for k in table if wins[k] >= top - 1))
    for s in split:
        print("JUDGES DISAGREE, a person decides:", s)
    print("\nNext: gate failures come first, a person picks within the top tier, and this says nothing about motion.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack")
    p.add_argument("items", nargs="+")
    p.add_argument("--brief", required=True)
    p.add_argument("--purpose", required=True)
    p.add_argument("--criteria", required=True, help="semicolon-separated, specific and visible. Name what the purpose rules out: with vague points like 'fit for purpose', polish won")
    p.add_argument("--out", default="round1")
    p.add_argument("--seed", type=int, default=None)
    s = sub.add_parser("score")
    s.add_argument("dir")
    s.add_argument("replies")
    a = ap.parse_args()
    pack(a) if a.cmd == "pack" else score(a)


if __name__ == "__main__":
    main()
