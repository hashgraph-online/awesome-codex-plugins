"""Items 1, 2, 3: does anything lead the eye, is one thing bigger than the rest, how full is the frame."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from mj_common import check, fmt_t, grab, label_frame, th


def _center_surround(lab: np.ndarray) -> np.ndarray:
    out = np.zeros(lab.shape[:2], np.float32)
    for ch in range(3):
        c = lab[..., ch]
        for s_small, s_big in ((2, 16), (4, 32)):
            d = np.abs(cv2.GaussianBlur(c, (0, 0), s_small) - cv2.GaussianBlur(c, (0, 0), s_big))
            out += d * (1.0 if ch == 0 else 1.4)
    return out


def _spectral_residual(gray: np.ndarray) -> np.ndarray:
    """Hou and Zhang 2007, on a 64 px thumbnail."""
    small = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32)
    f = np.fft.fft2(small)
    log_amp = np.log(np.abs(f) + 1e-6)
    residual = log_amp - cv2.blur(log_amp, (3, 3))
    sal = np.abs(np.fft.ifft2(np.exp(residual + 1j * np.angle(f)))) ** 2
    sal = cv2.GaussianBlur(sal.astype(np.float32), (0, 0), 2.5)
    return cv2.resize(sal, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_LINEAR)


def attention_map(bgr: np.ndarray, motion: np.ndarray | None = None, boxes: list | None = None) -> np.ndarray:
    """A fast free stand-in for an eye model: contrast, colour, plus motion and known faces or text."""
    lab = cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    cs = _center_surround(lab)
    sr = _spectral_residual(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
    def norm(x):
        lo, hi = np.percentile(x, 1), np.percentile(x, 99.5)
        return np.clip((x - lo) / max(hi - lo, 1e-6), 0, 1)
    a = 0.65 * norm(cs) + 0.35 * norm(sr)
    if motion is not None:
        a = a + 0.8 * norm(cv2.GaussianBlur(motion.astype(np.float32), (0, 0), 3))
    for b in boxes or []:
        x, y, w, h = [int(v) for v in b]
        a[max(y, 0):y + h, max(x, 0):x + w] += 0.6
    a = cv2.GaussianBlur(a, (0, 0), 3)
    return a / max(a.max(), 1e-6)


def focus_facts(a: np.ndarray) -> dict:
    h, w = a.shape
    flat = a.reshape(-1)
    total = float(flat.sum()) or 1.0
    top = np.sort(flat)[::-1][: max(1, int(0.05 * flat.size))]
    top5 = float(top.sum()) / total
    p = flat / total
    entropy = float(-(p[p > 0] * np.log2(p[p > 0])).sum() / np.log2(flat.size))
    mask = (a >= 0.5).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    blobs = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < 0.001 * w * h:
            continue
        blobs.append({"area": int(area), "mass": float(a[labels == i].sum()),
                      "cx": float((stats[i, 0] + stats[i, 2] / 2) / w), "cy": float((stats[i, 1] + stats[i, 3] / 2) / h)})
    blobs.sort(key=lambda b: -b["mass"])
    mass = sum(b["mass"] for b in blobs) or 1.0
    dominance = blobs[0]["mass"] / mass if blobs else 0.0
    areas = sorted((b["area"] for b in blobs), reverse=True)
    area_ratio = areas[0] / max(areas[1], 1) if len(areas) > 1 else None
    return {"top5_mass": round(top5, 3), "entropy": round(entropy, 3), "peaks": len(blobs), "dominance": round(float(dominance), 3),
            "biggest_over_second": round(float(area_ratio), 2) if area_ratio else None,
            "focus_xy": [round(blobs[0]["cx"], 3), round(blobs[0]["cy"], 3)] if blobs else None}


def _subband_entropy(gray: np.ndarray) -> float:
    """Entropy of a small pyramid's bands, after Rosenholtz et al. 2007."""
    total, g = 0.0, gray.astype(np.float32)
    for _ in range(3):
        down = cv2.pyrDown(g)
        up = cv2.pyrUp(down, dstsize=(g.shape[1], g.shape[0]))
        band = g - up
        hist, _ = np.histogram(band, bins=64, range=(-64, 64))
        p = hist / max(hist.sum(), 1)
        total += float(-(p[p > 0] * np.log2(p[p > 0])).sum())
        g = down
    return total / 3


def clutter_facts(bgr: np.ndarray) -> dict:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 160)
    density = float((edges > 0).mean())
    n, _, stats, _ = cv2.connectedComponentsWithStats(cv2.dilate(edges, np.ones((3, 3), np.uint8)), 8)
    objects = int(((stats[1:, cv2.CC_STAT_AREA] >= 0.0006 * gray.size)).sum()) if n > 1 else 0
    return {"edge_density": round(density, 4), "subband_entropy": round(_subband_entropy(gray), 3), "element_count": objects}


def attention_checks(path: str, probe, shots: list[dict], faces_by_t: dict, ev: Path, product_box_fn=None) -> list[dict]:
    rows = []
    overlays = []
    for s in shots:
        if s["duration"] < 0.2:
            continue
        for frac in (0.5,):
            t = s["start"] + frac * s["duration"]
            f = grab(path, t, 480)
            f2 = grab(path, t + 0.08, 480)
            if f is None:
                continue
            motion = None
            if f2 is not None and f2.shape == f.shape:
                motion = cv2.absdiff(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY))
            a = attention_map(f, motion)
            ff = focus_facts(a)
            cf = clutter_facts(f)
            row = {"shot": s["index"], "t": round(t, 2), "shot_start": s["start"], "shot_end": s["end"], **ff, **cf,
                   "sharpness": round(float(cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()), 1)}
            if product_box_fn:
                pb = product_box_fn(t)
                if pb:
                    x, y, w, h = [int(v) for v in pb]
                    mask = np.zeros(a.shape, bool)
                    mask[y:y + h, x:x + w] = True
                    row["product_area"] = round(float(mask.mean()), 4)
                    row["attention_on_product"] = round(float(a[mask].sum() / max(a.sum(), 1e-6)), 3)
            rows.append(row)
            heat = cv2.applyColorMap((a * 255).astype(np.uint8), cv2.COLORMAP_JET)
            overlays.append(label_frame(cv2.addWeighted(f, 0.55, heat, 0.45, 0), f"{fmt_t(t)} peaks {ff['peaks']} dom {ff['dominance']}"))
    if not rows:
        return []

    no_lead = [r for r in rows if r["peaks"] >= th("no_lead_peaks") and r["dominance"] < th("no_lead_dominance")]
    same_size = [r for r in rows if r["peaks"] >= 4 and r["biggest_over_second"] and r["biggest_over_second"] < th("blob_scale_ratio")]
    crowded = [r for r in rows if r["edge_density"] > th("clutter_edges") or r["element_count"] > th("clutter_elements")]
    sheet = None
    if overlays:
        h, w = overlays[0].shape[:2]
        cols = 5
        tiles = []
        for i in range(0, len(overlays), cols):
            row = overlays[i:i + cols]
            while len(row) < cols:
                row.append(np.zeros((h, w, 3), np.uint8))
            tiles.append(cv2.hconcat([cv2.resize(x, (w, h)) for x in row]))
        ev.mkdir(parents=True, exist_ok=True)
        sheet = str(ev / "attention_sheet.jpg")
        im = cv2.vconcat(tiles)
        k = min(1.0, 2400 / im.shape[1])
        cv2.imwrite(sheet, cv2.resize(im, None, fx=k, fy=k), [cv2.IMWRITE_JPEG_QUALITY, 85])

    def ev_rows(lst):
        return [{"t": r["shot_start"], "t_end": r["shot_end"], "at": r["t"], "shot": r["shot"], "peaks": r["peaks"], "dominance": r["dominance"], "biggest_over_second": r["biggest_over_second"],
                 "edge_density": r["edge_density"], "element_count": r["element_count"]} for r in lst[:10]]

    n = len(rows)
    out = [
        check("leads_the_eye", "2 nothing leads the eye", "flagged" if no_lead else "clear",
              {"shots_measured": n, "shots_without_lead": len(no_lead), "share": round(len(no_lead) / n, 3),
               "median_dominance": round(float(np.median([r["dominance"] for r in rows])), 3),
               "median_peaks": float(np.median([r["peaks"] for r in rows])), "attention_sheet": sheet, "per_shot": rows},
              ev_rows(no_lead), ["no_lead_peaks", "no_lead_dominance"],
              note="A fast contrast, colour and motion model, not an eye tracker. Look at the heat map sheet before you call it."),
        check("object_scale", "1 everything is the same size", "flagged" if same_size else "clear",
              {"shots_measured": n, "shots_same_size": len(same_size)}, ev_rows(same_size), ["blob_scale_ratio"]),
        check("frame_load", "3 too much on screen", "flagged" if crowded else "clear",
              {"shots_measured": n, "shots_over_limit": len(crowded), "median_edge_density": round(float(np.median([r["edge_density"] for r in rows])), 4),
               "median_elements": float(np.median([r["element_count"] for r in rows])),
               "median_subband_entropy": round(float(np.median([r["subband_entropy"] for r in rows])), 3)},
              ev_rows(crowded), ["clutter_edges", "clutter_elements"]),
    ]
    sharp = [r["sharpness"] for r in rows]
    mid = float(np.median(sharp))
    soft = [r for r in rows if r["sharpness"] < th("soft_shot_ratio") * mid and mid > 20]
    evs = []
    for r in soft[:6]:
        g = grab(path, r["t"], 720)
        p = ev / f"soft_{r['shot']}.jpg"
        if g is not None:
            ev.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(p), label_frame(g, f"{fmt_t(r['t'])} sharpness {r['sharpness']}, median {mid:.0f}"), [cv2.IMWRITE_JPEG_QUALITY, 90])
        evs.append({"t": r["t"], "shot": r["shot"], "sharpness": r["sharpness"], "median_of_film": round(mid, 1), "evidence": str(p)})
    out.append(check("soft_shot", "broken frames", "flagged" if soft else "clear", {"median_sharpness": round(mid, 1), "soft_shots": len(soft)}, evs, ["soft_shot_ratio"],
                     note="Sharpness also tracks framing, so a smooth wide shot reads soft. Open the frame."))
    if product_box_fn and any("attention_on_product" in r for r in rows):
        have = [r for r in rows if "attention_on_product" in r]
        out.append(check("product_attention", "3 product is not readable", "info",
                         {"shots_with_product": len(have), "shots_total": n,
                          "median_area": round(float(np.median([r["product_area"] for r in have])), 4),
                          "median_attention": round(float(np.median([r["attention_on_product"] for r in have])), 3)}))
    return out
