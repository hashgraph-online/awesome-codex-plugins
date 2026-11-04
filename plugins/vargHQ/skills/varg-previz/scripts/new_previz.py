#!/usr/bin/env python3
"""Scaffold a previz into a project folder.

  python3 new_previz.py <project_dir> [--title T] [--aspect 9:16] [--bpm 120] [--audio assets/track.mp3] [--force]

- copies the template app to <project_dir>/previz/ (no examples, no sample data); with --force on an existing
  previz/ it refreshes only the app files and keeps config.json, sets.js, shots.js, props.js, pack.json and edits
- if <project_dir>/storyboard.json is missing, writes the sample storyboard there so the app opens at once
- writes previz/config.json (paths relative to previz/) and previz/seedance/pack.json with runs pre-grouped:
  one location per run, runs of at most 11 s, in timeline order inside each location
- with your own storyboard, js/shots.js starts empty (auto cameras from the storyboard's "camera" words)
Then: python3 <project_dir>/previz/serve.py
"""
import argparse, json, shutil, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TPL = SKILL / "templates" / "previz"
MAX_RUN = 11.0
APP_FILES = ["index.html", "serve.py", "README.md", "js/main.js", "js/rig.js", "js/autocam.js", "vendor/three.module.min.js",
             "seedance/tools/build_pack.py", "seedance/tools/capture.mjs"]

EMPTY_SHOTS = '''// Per-shot previz: add an entry only where a shot needs animation or a hand-made camera.
// See the header of the template's shots.js (and examples/space-opera/shots.js) for the fields.
import * as THREE from 'three';
import { pose, walk, talk } from './props.js';

const cl = x => Math.max(0, Math.min(1, x));
export const ramp = (x, a, b) => cl((x - a) / (b - a));
export const sm = x => x * x * (3 - 2 * x);
export const V = (x, y, z) => new THREE.Vector3(x, y, z);
export const cam = (ap, at, af, bp, bt, bf, ease = 'inOut', ar = 0, br = 0) =>
  ({ a: { p: ap, t: at, fov: af, roll: ar }, b: { p: bp || ap, t: bt || at, fov: bf ?? af, roll: br }, ease });

export const SHOTS = {
  // s01: { anim(S, c) { pose(S.o.a, [['sit', 1], ['phone', 1]]); } },
};
'''


def group_runs(shots):
    """Scene grouping: per location (first appearance order), consecutive-in-time runs of <= MAX_RUN seconds."""
    order, by = [], {}
    for s in shots:
        if s.get("source") in ("reuse", "code"):
            continue
        k = s.get("scene") or "scene"
        if k not in by:
            order.append(k); by[k] = []
        by[k].append(s)
    runs = []
    for k in order:
        cur, t = [], 0.0
        for s in sorted(by[k], key=lambda x: x["start"]):
            d = s["end"] - s["start"]
            if cur and t + d > MAX_RUN:
                runs.append((k, cur)); cur, t = [], 0.0
            cur.append(s); t += d
        if cur:
            runs.append((k, cur))
    out, count, used = [], {}, set(order)  # scene names are reserved, so "A" split in two never collides with a scene "A1"
    for k, ss in runs:
        if sum(1 for x, _ in runs if x == k) == 1:
            key = k
        else:
            while True:
                count[k] = count.get(k, 0) + 1
                key = f"{k}{count[k]}"
                if key not in used:
                    break
        used.add(key)
        out.append({"key": key, "title": k.replace("_", " "), "shots": [s["id"] for s in ss], "refs": [], "notes": []})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--title")
    ap.add_argument("--aspect")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--audio", help="path relative to the project root")
    ap.add_argument("--force", action="store_true",
                    help="refresh the app files of an existing previz/ (keeps config, sets, shots, props, pack and edits)")
    a = ap.parse_args()
    root = Path(a.project).resolve()
    root.mkdir(parents=True, exist_ok=True)
    dst = root / "previz"
    if dst.exists() and not a.force:
        sys.exit(f"{dst} exists; use --force to refresh the app files (your config, sets, shots, props, pack and edits are kept)")

    sb_path = root / "storyboard.json"
    sample = not sb_path.exists()
    if sample:
        shutil.copy(TPL / "sample" / "storyboard.json", sb_path)
    sb = json.loads(sb_path.read_text())

    refresh = dst.exists()
    if refresh:  # only the app itself; everything a project edits stays
        for f in APP_FILES:
            (dst / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(TPL / f, dst / f)
    else:
        ignore = shutil.ignore_patterns("examples", "sample", "data", "config.json", "pack.json", "__pycache__", ".DS_Store")
        shutil.copytree(TPL, dst, ignore=ignore)
    (dst / "data").mkdir(exist_ok=True)
    if not (dst / "data" / "edits.json").exists():
        (dst / "data" / "edits.json").write_text('{"version": 1, "shots": {}}\n')
    if not sample and not refresh:
        (dst / "js" / "shots.js").write_text(EMPTY_SHOTS)

    tcfg = json.loads((TPL / "config.json").read_text())
    cfg = {
        "title": a.title or sb.get("title") or root.name,
        "storyboard": "../storyboard.json",
        "audio": f"../{a.audio}" if a.audio else (f"../{sb['song']}" if sb.get("song") else None),
        "bpm": a.bpm or sb.get("bpm"),
        "aspect": a.aspect or sb.get("aspect") or "9:16",
        "stills": None,
        "scenes": tcfg["scenes"] if sample else {},
        "scale": tcfg["scale"],
        "hud": tcfg["hud"] if sample else [],
        "planFile": "camera_plan.md",
    }
    cfg_path = dst / "config.json"
    if not cfg_path.exists():
        cfg_path.write_text(json.dumps(cfg, indent=1, ensure_ascii=False) + "\n")

    pack_path = dst / "seedance" / "pack.json"
    if not pack_path.exists():
        if sample:
            shutil.copy(TPL / "seedance" / "pack.json", pack_path)
        else:
            pack = {"title": cfg["title"], "model": "byteplus:dreamina-seedance-2-5-260628", "resolution": "480p",
                    "credits_per_second": None, "look": "", "refs": {}, "runs": group_runs(sb["shots"]),
                    "reuse": {s["id"]: "reuse" for s in sb["shots"] if s.get("source") == "reuse"}, "lipsync": []}
            pack_path.write_text(json.dumps(pack, indent=1, ensure_ascii=False) + "\n")

    print(f"previz ready: {dst}")
    print(f"  storyboard: {sb_path}{' (sample)' if sample else ''} · {len(sb['shots'])} shots · aspect {cfg['aspect']}")
    print(f"  run:   python3 {dst / 'serve.py'}")
    print(f"  check: python3 {dst / 'seedance/tools/build_pack.py'} --check")


if __name__ == "__main__":
    main()
