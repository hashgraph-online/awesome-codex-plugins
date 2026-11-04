#!/usr/bin/env python3
"""face_check.py - objective identity check with InsightFace ArcFace (buffalo_l).

Compares the largest face in each image with one or more reference faces
(cosine similarity of L2-normalised ArcFace embeddings) and reports, per group
(condition), how many faces were found, mean/min similarity to each reference
and the mean pairwise similarity among the group's own faces (consistency).

Image spec (refs and images):  [NAME=]PATH[@CROP]
  CROP = RxC:r,c          grid cell, 0-indexed (e.g. sheet.png@2x3:1,0 = bottom-left of a 3x2 sheet)
       = x0,y0,x1,y1      pixel box
  NAME defaults to the file stem (+ _r<r>c<c> for a grid cell).

Example:
  python face_check.py \
    --ref grey=img/sheet_grey.png@2x3:1,0 --ref look=img/sheet_look.png@2x3:1,0 \
    --group-regex '^s\\d+_(.+)$' --out results.csv img/s*_*.png

License: InsightFace's pretrained model packs (buffalo_l, antelopev2) are for non-commercial research
only. For commercial work swap in AuraFace (Apache 2.0, huggingface.co/fal/AuraFace-v1, same ArcFace-style
512-d embedding) or a licensed ArcFace, and re-check the threshold on your own same/different pairs.

Install: uv venv && uv pip install insightface onnxruntime opencv-python-headless numpy

Threshold: InsightFace's own demo (web-demos/src_recognition/main.py) says
cos >= 0.28 same person, 0.20-0.28 likely the same, < 0.20 not the same.
"""
from __future__ import annotations

import argparse
import csv
import glob
import itertools
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

SAME_T = 0.28
LIKELY_T = 0.20


@dataclass
class Spec:
    name: str
    path: Path
    crop: str | None = None
    group: str = "all"
    img: np.ndarray | None = None
    face: dict = field(default_factory=dict)
    emb: np.ndarray | None = None


def parse_spec(s: str) -> list[Spec]:
    name = None
    if "=" in s.split("@")[0]:
        name, s = s.split("=", 1)
    crop = None
    if "@" in s:
        s, crop = s.rsplit("@", 1)
    paths = sorted(glob.glob(s)) if any(ch in s for ch in "*?[") else [s]
    out = []
    for p in paths:
        p = Path(p)
        n = name or p.stem
        if crop and not name and re.match(r"^\d+x\d+:\d+,\d+$", crop):
            r, c = crop.split(":")[1].split(",")
            n = f"{p.stem}_r{r}c{c}"
        out.append(Spec(n, p, crop))
    return out


def load(spec: Spec) -> np.ndarray:
    img = cv2.imread(str(spec.path))
    if img is None:
        raise SystemExit(f"cannot read {spec.path}")
    if spec.crop:
        h, w = img.shape[:2]
        m = re.match(r"^(\d+)x(\d+):(\d+),(\d+)$", spec.crop)
        if m:
            R, C, r, c = map(int, m.groups())
            y0, y1 = h * r // R, h * (r + 1) // R
            x0, x1 = w * c // C, w * (c + 1) // C
        else:
            x0, y0, x1, y1 = map(int, spec.crop.split(","))
        img = img[y0:y1, x0:x1].copy()
    return img


def r32(v: int) -> int:
    return max(32, int(np.ceil(v / 32.0)) * 32)


class Engine:
    def __init__(self, model: str, root: str | None):
        from insightface.app import FaceAnalysis

        kw = {"name": model, "providers": ["CPUExecutionProvider"]}
        if root:
            kw["root"] = root
        self.app = FaceAnalysis(**kw)
        self.app.prepare(ctx_id=-1, det_size=(640, 640), det_thresh=0.5)

    def detect(self, img: np.ndarray):
        """Multi-pass: 640 det size -> native resolution -> 2x upscale with lower threshold,
        plus a padded pass for faces that fill the frame. First pass that finds a face wins."""
        h, w = img.shape[:2]
        pad = cv2.copyMakeBorder(img, h // 4, h // 4, w // 4, w // 4, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        up = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        passes = [
            ("640", img, (640, 640), 0.5),
            ("native", img, (r32(w), r32(h)), 0.5),
            ("padded", pad, (640, 640), 0.5),
            ("2x_t0.35", up, (r32(2 * w), r32(2 * h)), 0.35),
        ]
        for tag, im, size, thr in passes:
            self.app.prepare(ctx_id=-1, det_size=size, det_thresh=thr)
            faces = self.app.get(im)
            if faces:
                return tag, im, faces
        return None, img, []


def analyse(engine: Engine, spec: Spec, crops_dir: Path | None):
    spec.img = load(spec)
    tag, im, faces = engine.detect(spec.img)
    if not faces:
        spec.face = {"detected": 0, "n_faces": 0, "pass": "none"}
        return
    f = max(faces, key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]))
    scale = {"2x_t0.35": 2.0}.get(tag, 1.0)
    bw = (f.bbox[2] - f.bbox[0]) / scale
    bh = (f.bbox[3] - f.bbox[1]) / scale
    pose = getattr(f, "pose", None)
    spec.emb = f.normed_embedding.astype(np.float32)
    spec.face = {
        "detected": 1,
        "n_faces": len(faces),
        "pass": tag,
        "det_score": round(float(f.det_score), 3),
        "face_w": int(round(bw)),
        "face_h": int(round(bh)),
        # pose from the 1k3d68 landmark model: pitch, yaw, roll in degrees
        "pitch": round(float(pose[0]), 1) if pose is not None else "",
        "yaw": round(float(pose[1]), 1) if pose is not None else "",
        "roll": round(float(pose[2]), 1) if pose is not None else "",
        "emb_norm": round(float(np.linalg.norm(f.embedding)), 2),
    }
    if crops_dir:
        from insightface.utils import face_align

        aligned = face_align.norm_crop(im, f.kps, image_size=112)
        x0, y0, x1, y1 = [int(v) for v in f.bbox]
        hh, ww = im.shape[:2]
        mx, my = int((x1 - x0) * 0.3), int((y1 - y0) * 0.3)
        box = im[max(0, y0 - my):min(hh, y1 + my), max(0, x0 - mx):min(ww, x1 + mx)]
        box = cv2.resize(box, (224, int(224 * box.shape[0] / max(1, box.shape[1]))))
        cv2.imwrite(str(crops_dir / f"{spec.name}.jpg"), box)
        cv2.imwrite(str(crops_dir / f"{spec.name}_aligned.jpg"), aligned)


def verdict(s: float) -> str:
    return "same" if s >= SAME_T else ("likely" if s >= LIKELY_T else "different")


def main():
    global SAME_T, LIKELY_T
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+", help="image specs [NAME=]PATH[@CROP], globs allowed")
    ap.add_argument("--ref", action="append", required=True, help="reference spec [NAME=]PATH[@CROP] (repeatable; first is primary)")
    ap.add_argument("--group-regex", default=None, help="regex on image NAME; first non-empty capture = group. No match -> 'other'")
    ap.add_argument("--out", default="face_check.csv")
    ap.add_argument("--summary", default=None, help="summary JSON (default: <out>_summary.json)")
    ap.add_argument("--crops", default=None, help="dir to save face crops for eyeballing")
    ap.add_argument("--model", default="buffalo_l")
    ap.add_argument("--model-root", default=None, help="insightface model root (default ~/.insightface)")
    ap.add_argument("--threshold", type=float, default=SAME_T)
    ap.add_argument("--likely", type=float, default=LIKELY_T)
    a = ap.parse_args()
    SAME_T, LIKELY_T = a.threshold, a.likely

    crops = Path(a.crops) if a.crops else None
    if crops:
        crops.mkdir(parents=True, exist_ok=True)
    eng = Engine(a.model, a.model_root)

    refs = [s for r in a.ref for s in parse_spec(r)]
    for r in refs:
        analyse(eng, r, crops)
        if r.emb is None:
            raise SystemExit(f"no face found in reference {r.name} ({r.path} {r.crop or ''})")
    imgs = [s for i in a.images for s in parse_spec(i)]
    rx = re.compile(a.group_regex) if a.group_regex else None
    for s in imgs:
        if rx:
            m = rx.search(s.name)
            s.group = next((g for g in m.groups() if g), m.group(0)) if m else "other"
        analyse(eng, s, crops)
        print(f"  {s.name:28s} {s.group:14s} pass={s.face['pass']:9s} det={s.face.get('det_score','-')} "
              f"face={s.face.get('face_w','-')}px yaw={s.face.get('yaw','-')} "
              + " ".join(f"{r.name}={float(s.emb @ r.emb):.3f}" for r in refs if s.emb is not None),
              file=sys.stderr)

    # reference-vs-reference
    ref_pairs = {f"{x.name}~{y.name}": round(float(x.emb @ y.emb), 4) for x, y in itertools.combinations(refs, 2)}

    # CSV
    cols = ["name", "group", "path", "crop", "detected", "n_faces", "pass", "det_score", "face_w", "face_h",
            "yaw", "pitch", "roll", "emb_norm"]
    for r in refs:
        cols += [f"sim_{r.name}", f"verdict_{r.name}"]
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for s in imgs:
            row = {"name": s.name, "group": s.group, "path": str(s.path), "crop": s.crop or "", **s.face}
            for r in refs:
                if s.emb is not None:
                    v = float(s.emb @ r.emb)
                    row[f"sim_{r.name}"], row[f"verdict_{r.name}"] = round(v, 4), verdict(v)
                else:
                    row[f"sim_{r.name}"], row[f"verdict_{r.name}"] = "", "no_face"
            w.writerow({k: row.get(k, "") for k in cols})

    # summary per group
    groups: dict[str, list[Spec]] = {}
    for s in imgs:
        groups.setdefault(s.group, []).append(s)
    summ = {"model": a.model, "threshold_same": SAME_T, "threshold_likely": LIKELY_T,
            "refs": [{"name": r.name, "path": str(r.path), "crop": r.crop, **r.face} for r in refs],
            "ref_pairs": ref_pairs, "groups": {}}
    for g, ss in groups.items():
        det = [s for s in ss if s.emb is not None]
        d = {"n_images": len(ss), "n_detected": len(det), "failed": [s.name for s in ss if s.emb is None]}
        for r in refs:
            sims = [float(s.emb @ r.emb) for s in det]
            d[f"vs_{r.name}"] = {
                "mean": round(float(np.mean(sims)), 4) if sims else None,
                "min": round(float(np.min(sims)), 4) if sims else None,
                "max": round(float(np.max(sims)), 4) if sims else None,
                "n_same": sum(v >= SAME_T for v in sims),
                "per_image": {s.name: round(v, 4) for s, v in zip(det, sims)},
            }
        pw = [float(x.emb @ y.emb) for x, y in itertools.combinations(det, 2)]
        d["pairwise"] = {"n_pairs": len(pw),
                         "mean": round(float(np.mean(pw)), 4) if pw else None,
                         "min": round(float(np.min(pw)), 4) if pw else None,
                         "n_same": sum(v >= SAME_T for v in pw)}
        summ["groups"][g] = d
    sp = a.summary or str(Path(a.out).with_suffix("")) + "_summary.json"
    Path(sp).write_text(json.dumps(summ, indent=1))

    # markdown table to stdout
    print(f"\nmodel={a.model}  same>={SAME_T}  likely>={LIKELY_T}  refs: " +
          ", ".join(f"{r.name} (det {r.face['det_score']}, {r.face['face_w']}px)" for r in refs))
    if ref_pairs:
        print("ref~ref: " + ", ".join(f"{k}={v:.3f}" for k, v in ref_pairs.items()))
    hdr = "| group | faces | " + " | ".join(f"mean vs {r.name} | min vs {r.name} | >= thr" for r in refs) + " | mean pairwise | min pairwise |"
    print(hdr)
    print("|" + "---|" * (hdr.count("|") - 1))
    for g, d in summ["groups"].items():
        cells = [g, f"{d['n_detected']}/{d['n_images']}"]
        for r in refs:
            v = d[f"vs_{r.name}"]
            cells += [f"{v['mean']:.3f}" if v["mean"] is not None else "-",
                      f"{v['min']:.3f}" if v["min"] is not None else "-",
                      f"{v['n_same']}/{d['n_detected']}"]
        p = d["pairwise"]
        cells += [f"{p['mean']:.3f}" if p["mean"] is not None else "-",
                  f"{p['min']:.3f}" if p["min"] is not None else "-"]
        print("| " + " | ".join(cells) + " |")
    print(f"\nwrote {a.out} and {sp}")


if __name__ == "__main__":
    main()
