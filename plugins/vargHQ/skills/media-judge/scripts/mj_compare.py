"""Item 12 and reference tests: how close is this video to its references, and how close to the template."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from mj_common import check, ciede2000, fmt_t, grab, label_frame, probe
from mj_frames import detect_shots, trace


def _phash(gray: np.ndarray) -> np.ndarray:
    small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    d = cv2.dct(small)[:8, :8]
    return (d > np.median(d)).reshape(-1)


def _palette(bgr: np.ndarray, k: int = 5) -> tuple[np.ndarray, np.ndarray]:
    small = cv2.resize(bgr, (64, 36), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab).reshape(-1, 3)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.5)
    cv2.setRNGSeed(7)
    _, labels, centers = cv2.kmeans(lab, k, None, crit, 2, cv2.KMEANS_PP_CENTERS)
    weights = np.bincount(labels.ravel(), minlength=k) / len(labels)
    return centers, weights


def _palette_distance(a, b) -> float:
    """Greedy weighted match of two palettes in CIEDE2000."""
    ca, wa = a
    cb, wb = b
    D = np.array([[ciede2000(x, y) for y in cb] for x in ca])
    wa, wb = wa.copy(), wb.copy()
    total, used = 0.0, 0.0
    for i, j in sorted(np.ndindex(D.shape), key=lambda ij: D[ij]):
        m = min(wa[i], wb[j])
        if m <= 0:
            continue
        total += m * D[i, j]
        used += m
        wa[i] -= m
        wb[j] -= m
    return total / max(used, 1e-6)


def _orient_hist(gray: np.ndarray) -> np.ndarray:
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    mag, ang = cv2.cartToPolar(gx, gy)
    h = np.histogram(ang % np.pi, bins=8, range=(0, np.pi), weights=mag)[0].astype(float)
    density = float((mag > 40).mean())
    h = h / max(h.sum(), 1e-6)
    return np.r_[h, density * 4]


def frame_features(bgr: np.ndarray) -> dict:
    small = cv2.resize(bgr, (256, int(256 * bgr.shape[0] / bgr.shape[1] / 2) * 2), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    lab = cv2.cvtColor(small.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    from mj_attention import attention_map
    att = cv2.resize(attention_map(small), (8, 8), interpolation=cv2.INTER_AREA)
    return {"gray": cv2.resize(gray, (128, 72), interpolation=cv2.INTER_AREA), "phash": _phash(gray), "palette": _palette(small), "orient": _orient_hist(gray),
            "att": att / max(att.sum(), 1e-6), "L": float(lab[..., 0].mean()), "contrast": float(lab[..., 0].std()), "chroma": float(np.hypot(lab[..., 1], lab[..., 2]).mean())}


def _ssim(a: np.ndarray, b: np.ndarray) -> float:
    a, b = a.astype(np.float32), b.astype(np.float32)
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    ma, mb = cv2.GaussianBlur(a, (11, 11), 1.5), cv2.GaussianBlur(b, (11, 11), 1.5)
    sa, sb = cv2.GaussianBlur(a * a, (11, 11), 1.5) - ma * ma, cv2.GaussianBlur(b * b, (11, 11), 1.5) - mb * mb
    sab = cv2.GaussianBlur(a * b, (11, 11), 1.5) - ma * mb
    return float((((2 * ma * mb + C1) * (2 * sab + C2)) / ((ma * ma + mb * mb + C1) * (sa + sb + C2))).mean())


def feature_distance(x: dict, y: dict) -> dict:
    gx, gy = x["gray"], y["gray"]
    if gx.shape != gy.shape:
        gy = cv2.resize(gy, (gx.shape[1], gx.shape[0]))
    return {
        "structure": 1 - _ssim(gx, gy),
        "phash": float((x["phash"] != y["phash"]).mean()),
        "palette": _palette_distance(x["palette"], y["palette"]) / 50,
        "composition": float(np.abs(x["att"] - y["att"]).sum() / 2),
        "texture": float(np.abs(x["orient"] - y["orient"]).sum() / 2),
        "tone": float(abs(x["L"] - y["L"]) / 50 + abs(x["contrast"] - y["contrast"]) / 30 + abs(x["chroma"] - y["chroma"]) / 40),
    }


def blend(d: dict) -> float:
    return 0.2 * d["structure"] + 0.1 * d["phash"] + 0.3 * d["palette"] + 0.15 * d["composition"] + 0.1 * d["texture"] + 0.15 * d["tone"]


def video_profile(path: str, max_shots: int = 60) -> dict:
    meta = probe(path, check_decode=False)
    tr = trace(path, meta.pts, meta.v_start)
    shots = detect_shots(tr)
    fps = meta.fps or 24
    motion = []
    keys = []
    for s in shots[:max_shots]:
        a, b = s["first_frame"], s["last_frame"]
        motion.append(float(np.median(tr.mad[a + 1:b + 1])) if b > a else 0.0)
        f = grab(path, s["start"] + 0.5 * s["duration"])
        if f is None:
            continue
        keys.append({"t": s["start"] + 0.5 * s["duration"], "duration": s["duration"], "motion": motion[-1], "shot": s["index"], **frame_features(f)})
    durs = np.array([k["duration"] for k in keys]) if keys else np.zeros(0)
    return {"path": path, "duration": meta.duration, "size": [meta.width, meta.height], "fps": fps, "shots": len(shots), "keys": keys,
            "asl": float(durs.mean()) if len(durs) else 0.0, "shot_cv": float(durs.std() / max(durs.mean(), 1e-6)) if len(durs) else 0.0,
            "motion": float(np.median(motion)) if motion else 0.0}


def align(p: dict, r: dict) -> list[tuple[int, int, float]]:
    """DTW over shots using the blended picture distance, with a small time-position prior."""
    a, b = p["keys"], r["keys"]
    if not a or not b:
        return []
    D = np.zeros((len(a), len(b)))
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            pos = abs(x["t"] / max(p["duration"], 1e-6) - y["t"] / max(r["duration"], 1e-6))
            D[i, j] = blend(feature_distance(x, y)) + 0.15 * pos
    C = np.full((len(a) + 1, len(b) + 1), np.inf)
    C[0, 0] = 0
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            C[i, j] = D[i - 1, j - 1] + min(C[i - 1, j - 1], C[i - 1, j], C[i, j - 1])
    pairs, i, j = [], len(a), len(b)
    while i > 0 and j > 0:
        pairs.append((i - 1, j - 1, float(D[i - 1, j - 1])))
        step = np.argmin([C[i - 1, j - 1], C[i - 1, j], C[i, j - 1]])
        if step == 0:
            i, j = i - 1, j - 1
        elif step == 1:
            i -= 1
        else:
            j -= 1
    return pairs[::-1]


def pair_facts(p: dict, r: dict) -> dict:
    pairs = align(p, r)
    rows = []
    for i, j, _ in pairs:
        d = feature_distance(p["keys"][i], r["keys"][j])
        rows.append({"ours_t": round(p["keys"][i]["t"], 2), "ref_t": round(r["keys"][j]["t"], 2),
                     "ours_dur": round(p["keys"][i]["duration"], 2), "ref_dur": round(r["keys"][j]["duration"], 2),
                     **{k: round(v, 3) for k, v in d.items()}})
    keys = ["structure", "phash", "palette", "composition", "texture", "tone"]
    mean = {k: round(float(np.mean([x[k] for x in rows])), 3) for k in keys} if rows else {}
    ours_dur = np.array([p["keys"][i]["duration"] for i, _, _ in pairs]) if pairs else np.zeros(0)
    ref_dur = np.array([r["keys"][j]["duration"] for _, j, _ in pairs]) if pairs else np.zeros(0)
    rhythm = float(np.mean(np.abs(np.log((ours_dur + 0.05) / (ref_dur + 0.05))))) if len(ours_dur) else 0.0
    return {"reference": Path(r["path"]).name, "shots_ours": p["shots"], "shots_ref": r["shots"], "asl_ours_s": round(p["asl"], 2), "asl_ref_s": round(r["asl"], 2),
            "shot_length_variation_ours": round(p["shot_cv"], 2), "shot_length_variation_ref": round(r["shot_cv"], 2),
            "rhythm_log_ratio": round(rhythm, 3), "motion_ours": round(p["motion"], 2), "motion_ref": round(r["motion"], 2),
            "mean_distance": mean, "blend": round(float(np.mean([blend(x) for x in rows])) + 0.25 * min(rhythm, 1.0), 3) if rows else None, "pairs": rows}


def pair_sheet(p: dict, r: dict, facts: dict, out: Path, max_rows: int = 16) -> str | None:
    rows = sorted(facts["pairs"], key=lambda x: -blend(x))[:max_rows]
    rows.sort(key=lambda x: x["ours_t"])
    if not rows:
        return None
    tiles = []
    for x in rows:
        a = grab(p["path"], x["ours_t"], 480)
        b = grab(r["path"], x["ref_t"], 480)
        if a is None or b is None:
            continue
        b = cv2.resize(b, (480, int(480 * b.shape[0] / b.shape[1])))
        a = cv2.resize(a, (480, b.shape[0]))
        la = label_frame(a, f"OURS {fmt_t(x['ours_t'])} {x['ours_dur']}s")
        lb = label_frame(b, f"REF {fmt_t(x['ref_t'])} {x['ref_dur']}s  dist {blend(x):.2f}")
        tiles.append(cv2.hconcat([la, lb]))
    if not tiles:
        return None
    # two columns of pairs, so the sheet stays one readable image
    cols = 2
    h, w = tiles[0].shape[:2]
    canvas = []
    for i in range(0, len(tiles), cols):
        row = [cv2.resize(t, (w, h)) for t in tiles[i:i + cols]]
        while len(row) < cols:
            row.append(np.zeros((h, w, 3), np.uint8))
        canvas.append(cv2.hconcat(row))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), cv2.vconcat(canvas), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return str(out)


def compare_checks(path: str, refs: list[str], templates: list[str], ev: Path) -> list[dict]:
    res: list[dict] = []
    if not refs and not templates:
        return res
    ours = video_profile(path)
    ref_rows = []
    for i, r in enumerate(refs):
        rp = video_profile(r)
        f = pair_facts(ours, rp)
        f["sheet"] = pair_sheet(ours, rp, f, ev / f"reference_pairs_{i}.jpg")
        ref_rows.append(f)
    tpl_rows = []
    for i, r in enumerate(templates):
        rp = video_profile(r)
        f = pair_facts(ours, rp)
        f["sheet"] = pair_sheet(ours, rp, f, ev / f"template_pairs_{i}.jpg")
        tpl_rows.append(f)
    if ref_rows:
        res.append(check("reference_match", "compare with the reference", "info",
                         {"references": [{k: v for k, v in r.items() if k != "pairs"} for r in ref_rows]},
                         note="Lower distance means closer. Open the pair sheet. Numbers say where it differs, your eyes say whether it matters."))
    if ref_rows and tpl_rows:
        best_r = min(ref_rows, key=lambda r: r["blend"] if r["blend"] is not None else 9)
        best_t = min(tpl_rows, key=lambda r: r["blend"] if r["blend"] is not None else 9)
        families = {}
        for k in ("palette", "composition", "texture", "tone", "structure"):
            dr = best_r["mean_distance"].get(k)
            dt = best_t["mean_distance"].get(k)
            if dr is None or dt is None:
                continue
            families[k] = {"to_references": dr, "to_template": dt, "closer_to": "references" if dr < dt else "template"}
        tpl_wins = sum(1 for v in families.values() if v["closer_to"] == "template")
        margin = round(best_t["blend"] - best_r["blend"], 3)
        res.append(check("template_vs_references", "12 it looks like the template, not like the references", "flagged" if margin < 0 else "clear",
                         {"distance_to_references": best_r["blend"], "distance_to_template": best_t["blend"], "margin": margin,
                          "rhythm_to_references": best_r["rhythm_log_ratio"], "rhythm_to_template": best_t["rhythm_log_ratio"],
                          "feature_families_closer_to_template": tpl_wins, "families": families},
                         [{"t": 0, "evidence": best_t.get("sheet")}, {"t": 0, "evidence": best_r.get("sheet")}],
                         note="Margin is distance to template minus distance to references. Above 0 means closer to the references."))
    elif tpl_rows:
        res.append(check("template_distance", "12 it looks like the template", "info", {"templates": [{k: v for k, v in r.items() if k != "pairs"} for r in tpl_rows]}))
    return res
