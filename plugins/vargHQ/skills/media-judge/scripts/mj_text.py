"""Items 1, 3, 8, 11: what text is on screen, how big, how long, and whether its numbers hold still."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from mj_common import check, fmt_t, grab, have, label_frame, not_run, read_frames, run, th

_engine = None


def _load_engine():
    global _engine
    if _engine is not None:
        return _engine
    try:
        from rapidocr_onnxruntime import RapidOCR
        rapid = RapidOCR()

        def go(img):
            result, _ = rapid(img)
            out = []
            for box, text, conf in result or []:
                pts = np.array(box, float)
                x0, y0 = pts.min(axis=0)
                x1, y1 = pts.max(axis=0)
                out.append({"text": str(text).strip(), "conf": float(conf), "box": [float(x0), float(y0), float(x1 - x0), float(y1 - y0)]})
            return out
        _engine = ("rapidocr", go)
    except Exception:
        if have("tesseract"):
            _engine = ("tesseract", _tesseract)
        else:
            _engine = (None, None)
    return _engine


def _tesseract(img):
    import csv
    import io
    import subprocess
    ok, buf = cv2.imencode(".png", img)
    proc = subprocess.run(["tesseract", "stdin", "stdout", "--psm", "11", "tsv"], input=buf.tobytes(), capture_output=True)
    lines: dict[tuple, dict] = {}
    for row in csv.DictReader(io.StringIO(proc.stdout.decode("utf8", "ignore")), delimiter="\t", quoting=csv.QUOTE_NONE):
        txt = (row.get("text") or "").strip()
        if not txt or float(row.get("conf", -1)) < 30:
            continue
        key = (row["block_num"], row["par_num"], row["line_num"])
        x, y, w, h = (float(row[k]) for k in ("left", "top", "width", "height"))
        ln = lines.setdefault(key, {"words": [], "confs": [], "x0": x, "y0": y, "x1": x + w, "y1": y + h})
        ln["words"].append(txt)
        ln["confs"].append(float(row["conf"]) / 100)
        ln["x0"], ln["y0"] = min(ln["x0"], x), min(ln["y0"], y)
        ln["x1"], ln["y1"] = max(ln["x1"], x + w), max(ln["y1"], y + h)
    return [{"text": " ".join(l["words"]), "conf": float(np.mean(l["confs"])), "box": [l["x0"], l["y0"], l["x1"] - l["x0"], l["y1"] - l["y0"]]}
            for l in lines.values()]


def _iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = a[0], a[1], a[0] + a[2], a[1] + a[3]
    bx1, by1, bx2, by2 = b[0], b[1], b[0] + b[2], b[1] + b[3]
    ix = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union else 0.0


def _ratio(a: str, b: str) -> float:
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _digits(s: str) -> str:
    return re.sub(r"[^0-9]", "", s)


def _plausible(d: dict) -> bool:
    """The default OCR model invents lone CJK glyphs in dark textures. Keep real lines only."""
    s = d["text"]
    if len(s) < 2 or not re.search(r"[0-9A-Za-z\u00c0-\u024f\u0400-\u04ff\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]", s):
        return False
    if re.search(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]", s) and (len(s) < 3 or d["conf"] < 0.85):
        return False
    return d["conf"] >= 0.5


def read_text(path: str, probe, shots: list[dict], max_side: int = 1280) -> dict:
    """OCR at 2 fps plus every shot's middle frame. Returns one record per sampled frame and joined tracks."""
    name, ocr = _load_engine()
    if ocr is None:
        return {"engine": None, "samples": [], "tracks": []}
    dur = probe.duration or (probe.pts[-1] if probe.pts else 0)
    times = sorted({round(x, 2) for x in np.arange(0.1, max(dur, 0.2), 0.5)} | {round((s["start"] + s["end"]) / 2, 2) for s in shots})
    k = min(1.0, max_side / max(probe.width, probe.height))
    w = int(round(probe.width * k / 2)) * 2
    h = int(round(probe.height * k / 2)) * 2
    samples, tracks = [], []
    for t in times:
        f = grab(path, t, w)
        if f is None:
            continue
        dets = [d for d in ocr(f) if _plausible(d)]
        samples.append({"t": t, "dets": dets})
        for d in dets:
            best, best_score = None, 0.0
            for tr in tracks:
                if t - tr["t_last"] > 1.3:
                    continue
                iou = _iou(tr["box"], d["box"])
                same = _ratio(tr["last"], d["text"])
                both_digits = bool(_digits(tr["last"])) and bool(_digits(d["text"]))
                score = iou + same * (0.5 if iou > 0.05 else 0.25)
                if (iou > 0.25 and (same > 0.4 or both_digits)) or (same > 0.82 and iou > 0.02):
                    if score > best_score:
                        best, best_score = tr, score
            if best is None:
                tracks.append({"t0": t, "t_last": t, "box": list(d["box"]), "last": d["text"], "readings": [(t, d["text"], d["conf"])],
                               "heights": [d["box"][3]], "boxes": [(t, list(d["box"]))]})
            else:
                best["t_last"] = t
                best["box"] = list(d["box"])
                best["last"] = d["text"]
                best["readings"].append((t, d["text"], d["conf"]))
                best["heights"].append(d["box"][3])
                best["boxes"].append((t, list(d["box"])))
    return {"engine": name, "samples": samples, "tracks": tracks, "ocr_width": w, "ocr_height": h}


def _words(s: str) -> list[str]:
    # Addresses and code are not prose: drop any chunk holding a slash, an inner dot, an @ or an underscore.
    s = " ".join(c for c in s.split() if not re.search(r"[/@_]|\w\.\w", c))
    return re.findall(r"[A-Za-z][A-Za-z'’]*[A-Za-z]|[A-Za-z]", s)


def _splits_into_words(w: str, sp) -> bool:
    """True when a long token is several known words with the spaces lost."""
    n = len(w)
    ok = [False] * (n + 1)
    ok[0] = True
    for i in range(1, n + 1):
        for j in range(max(0, i - 14), i):
            piece = w[j:i]
            if ok[j] and (len(piece) >= 3 or piece in {"a", "i", "an", "as", "at", "be", "by", "do", "go", "he", "if", "in", "is", "it", "me", "my", "no", "of", "on", "or", "so", "to", "up", "us", "we"}) and sp.known([piece]):
                ok[i] = True
                break
    return ok[n]


def spelling_check(path: str, text: dict, allow: set[str], expected: list[str], ev: Path) -> list[dict]:
    covers = "11 a spelling mistake anywhere on screen"
    if not text["engine"]:
        return [not_run("spelling", covers, "No OCR engine. Install rapidocr-onnxruntime or tesseract.")]
    try:
        from spellchecker import SpellChecker
        sp = SpellChecker(distance=2)
    except Exception:
        return [not_run("spelling", covers, "pyspellchecker is not installed.")]
    allow_low = {a.lower() for a in allow}
    seen: dict[str, dict] = {}
    all_text = []
    for tr in text["tracks"]:
        best = Counter(r[1] for r in tr["readings"]).most_common(1)[0][0]
        all_text.append(best)
        n = len(tr["readings"])
        # A word misread in one frame and read right in others is OCR noise, not a typo.
        votes: Counter = Counter()
        for _, reading, _ in tr["readings"]:
            for w in set(x.lower() for x in _words(reading)):
                votes[w] += 1
        known_any = {w for w in votes if sp.known([w])}
        for _, reading, conf in tr["readings"]:
            for raw in _words(reading):
                w = raw.lower().strip("'’-")
                if len(w) < 3 or w in allow_low or w in known_any:
                    continue
                if raw.isupper() and len(raw) <= 3:
                    continue
                if re.search(r"[a-z][A-Z]", raw):  # CamelCase brand names
                    continue
                if len(w) >= 5 and _splits_into_words(w, sp):  # OCR dropped the spaces
                    continue
                if any(sp.known([p]) for p in w.replace("’", "'").split("'") if len(p) > 2) and "'" in w:
                    continue
                rec = seen.setdefault(w, {"word": raw, "t": tr["t0"], "frames": 0, "conf": 0.0, "in": best, "box": tr["box"], "track_frames": n})
                rec["frames"] += 1
                rec["conf"] = max(rec["conf"], conf)
    events = []
    for w, r in seen.items():
        steady = r["frames"] >= 2 or r["track_frames"] == 1
        if r["conf"] < th("ocr_word_conf") or not steady:
            continue
        sug = sp.correction(w)
        e = {"t": r["t"], "word": r["word"], "suggestion": sug if sug != w else None, "line": r["in"], "ocr_conf": round(r["conf"], 3),
             "seen_in_samples": r["frames"], "needs_eyes": True,
             "evidence": _crop(path, r["t"], r["box"], text, ev / f"spell_{re.sub(r'[^a-z0-9]', '_', w)}.jpg")}
        events.append(e)
    out = [check("spelling", covers, "flagged" if events else "clear",
                 {"engine": text["engine"], "words_flagged": len(events), "lines_read": all_text[:80]}, events[:40],
                 ["ocr_word_conf"], note="OCR candidates. Open each crop before you call it a typo.")]
    if expected:
        joined = " ".join(all_text).lower()
        missing = [line for line in expected if not _phrase_found(line.lower(), joined)]
        out.append(check("expected_text", covers, "flagged" if missing else "clear",
                         {"expected_lines": len(expected), "missing": missing, "seen_lines": all_text[:80]}))
    return out


def _phrase_found(line: str, hay: str) -> bool:
    if line in hay:
        return True
    n = len(line)
    best = 0.0
    for i in range(0, max(1, len(hay) - n + 1), max(1, n // 4)):
        best = max(best, _ratio(line, hay[i:i + n]))
    return best >= 0.82


def _crop(path: str, t: float, box: list[float], text: dict, out: Path) -> str | None:
    f = grab(path, t, text["ocr_width"])
    if f is None:
        return None
    x, y, w, h = box
    pad = int(max(h, 16))
    H, W = f.shape[:2]
    c = f[max(int(y) - pad, 0):min(int(y + h) + pad, H), max(int(x) - pad, 0):min(int(x + w) + pad, W)]
    if c.size == 0:
        return None
    k = max(1.0, 320 / max(c.shape[0], 1) if c.shape[0] < 160 else 1.0)
    c = cv2.resize(c, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), label_frame(c, fmt_t(t)), [cv2.IMWRITE_JPEG_QUALITY, 92])
    return str(out)


def _blocks(dets: list[dict]) -> list[dict]:
    """Join stacked lines of one size into one block, so a paragraph does not count as many items."""
    ds = sorted(dets, key=lambda d: d["box"][1])
    blocks: list[dict] = []
    for d in ds:
        x, y, w, h = d["box"]
        for b in blocks:
            same = 0.8 <= h / b["h"] <= 1.25
            gap = y - b["y1"]
            overlap = min(x + w, b["x1"]) - max(x, b["x0"])
            if same and -0.2 * h <= gap <= 0.9 * h and overlap > -0.5 * h:
                b["y1"] = y + h
                b["x0"], b["x1"] = min(b["x0"], x), max(b["x1"], x + w)
                b["n"] += 1
                b["text"] += " " + d["text"]
                break
        else:
            blocks.append({"x0": x, "x1": x + w, "y0": y, "y1": y + h, "h": h, "n": 1, "text": d["text"]})
    return blocks


def layout_checks(path: str, probe, text: dict, ev: Path, platform: str | None) -> list[dict]:
    if not text["engine"]:
        why = "No OCR engine."
        return [not_run(n, c, why) for n, c in [("text_scale", "1 everything is the same size"), ("text_load", "3 too much on screen"),
                                                ("reading_time", "3 too much on screen"), ("text_contrast", "3 product is not readable"),
                                                ("safe_zone", "3 product is not readable")]]
    H, W = text["ocr_height"], text["ocr_width"]
    same_frames, ratios, frames_text = [], [], 0
    loads = []
    for s in text["samples"]:
        dets = [d for d in s["dets"] if len(d["text"]) >= 2]
        words = sum(len(d["text"].split()) for d in dets)
        cover = sum(d["box"][2] * d["box"][3] for d in dets) / (W * H)
        loads.append({"t": s["t"], "words": words, "lines": len(dets), "text_cover": round(float(cover), 4)})
        if not dets:
            continue
        frames_text += 1
        blocks = _blocks(dets)
        if len(blocks) >= 2:
            hs = sorted(b["h"] for b in blocks)
            r = hs[-1] / max(hs[0], 1)
            ratios.append(r)
            if r < th("text_scale_ratio"):
                same_frames.append({"t": s["t"], "blocks": len(blocks), "largest_over_smallest": round(float(r), 2),
                                    "heights_px": [round(h, 1) for h in hs], "text": [b["text"][:40] for b in blocks][:6]})
    multi = max(len(ratios), 1)
    share = len(same_frames) / multi
    events = same_frames[:6]
    if events:
        events[0]["evidence"] = _whole(path, events[0]["t"], ev / "same_size.jpg")
    out = [check("text_scale", "1 everything is the same size",
                 "flagged" if share >= th("text_scale_share") and len(ratios) >= 2 else ("clear" if ratios else "info"),
                 {"frames_with_two_or_more_blocks": len(ratios), "same_size_frames": len(same_frames), "same_size_share": round(share, 3),
                  "median_largest_over_smallest": round(float(np.median(ratios)), 2) if ratios else None},
                 events, ["text_scale_ratio", "text_scale_share"])]

    peak = max(loads, key=lambda l: l["words"], default={"words": 0, "t": 0, "text_cover": 0, "lines": 0})
    heavy = [l for l in loads if l["words"] >= th("words_on_screen")]
    ev_load = []
    if heavy:
        e = dict(peak)
        e["t"], e["t_end"] = heavy[0]["t"], heavy[-1]["t"]
        e["peak_at"] = peak["t"]
        e["evidence"] = _whole(path, peak["t"], ev / "text_load.jpg")
        ev_load.append(e)
    out.append(check("text_load", "3 too much on screen", "flagged" if heavy else "clear",
                     {"peak_words": peak["words"], "peak_at": peak["t"], "peak_text_cover": peak["text_cover"],
                      "samples_over_limit": len(heavy), "samples": len(loads)}, ev_load, ["words_on_screen"]))

    # reading time per text track
    rt = []
    for tr in text["tracks"]:
        best = Counter(r[1] for r in tr["readings"]).most_common(1)[0][0]
        if len(best.split()) < 3:
            continue
        dur = tr["t_last"] - tr["t0"] + 1.0  # OCR samples at 2 fps, so this is the longest it could have stayed
        cps = len(best) / dur
        if cps > th("reading_cps"):
            rt.append({"t": tr["t0"], "t_end": tr["t_last"], "text": best[:80], "chars_per_s": round(cps, 1), "on_screen_s": round(dur, 2)})
    out.append(check("reading_time", "3 too much on screen", "flagged" if rt else "clear", {"tracks_over_limit": len(rt)}, rt[:10], ["reading_cps"],
                     note="OCR samples at 2 fps, so on-screen time is an upper bound and this check errs on the kind side."))

    # contrast of text against what is behind it
    low, tested = [], 0
    for s in text["samples"][::2]:
        dets = [d for d in s["dets"] if len(d["text"]) >= 4 and d["conf"] >= 0.8]
        if not dets:
            continue
        f = grab(path, s["t"], W)
        if f is None:
            continue
        for d in dets[:6]:
            x, y, w, h = [int(v) for v in d["box"]]
            c = f[max(y, 0):y + h, max(x, 0):x + w]
            if c.size < 30:
                continue
            ratio = _contrast(c)
            tested += 1
            if ratio < th("text_contrast"):
                low.append({"t": s["t"], "text": d["text"][:60], "contrast_ratio": round(ratio, 2)})
    if low:
        worst = min(low, key=lambda e: e["contrast_ratio"])
        worst["evidence"] = _whole(path, worst["t"], ev / "low_contrast.jpg")
    out.append(check("text_contrast", "3 product is not readable", "flagged" if low else "clear", {"lines_tested": tested, "below_limit": len(low)},
                     sorted(low, key=lambda e: e["contrast_ratio"])[:8], ["text_contrast"]))

    # smallest text relative to frame height
    small = []
    for s in text["samples"]:
        for d in s["dets"]:
            pct = d["box"][3] / min(H, W) * 100
            if pct < th("text_min_height_pct") and d["conf"] > 0.7 and len(d["text"]) >= 3:
                small.append({"t": s["t"], "text": d["text"][:50], "height_pct_of_short_side": round(pct, 2)})
    out.append(check("text_size_floor", "3 product is not readable", "flagged" if small else "clear", {"count": len(small)},
                     small[:8], ["text_min_height_pct"]))

    # platform safe zones
    vertical = H > W
    if platform in {"tiktok", "reels", "shorts"} or (platform is None and vertical):
        p = platform or "reels"
        zone = SAFE_ZONES[p]
        hits = []
        for tr in text["tracks"]:
            x, y, w, h = tr["box"]
            fx0, fy0, fx1, fy1 = x / W, y / H, (x + w) / W, (y + h) / H
            sides = []
            if fy0 < zone["top"]:
                sides.append("top")
            if fy1 > 1 - zone["bottom"]:
                sides.append("bottom")
            if fx1 > 1 - zone["right"]:
                sides.append("right")
            if fx0 < zone["left"]:
                sides.append("left")
            if sides:
                hits.append({"t": tr["t0"], "text": tr["last"][:60], "under_ui": sides})
        out.append(check("safe_zone", "3 product is not readable", "flagged" if hits else "clear",
                         {"platform": p, "zone": zone, "tracks_under_ui": len(hits)}, hits[:10],
                         note="Each platform changes its interface. Zones were read on 2026-11-03."))
    else:
        out.append(check("safe_zone", "3 product is not readable", "info", {"platform": platform}, note="Applies to vertical formats only."))
    return out


SAFE_ZONES = {
    # Meta's numbers are official. TikTok and Shorts are third-party readings of official files.
    "reels": {"top": 0.14, "bottom": 0.35, "right": 0.06, "left": 0.06},
    "tiktok": {"top": 0.125, "bottom": 0.344, "right": 0.111, "left": 0.111},
    "shorts": {"top": 0.15, "bottom": 0.35, "right": 0.178, "left": 0.044},
}


def _rel_lum(bgr: np.ndarray) -> np.ndarray:
    x = bgr.astype(np.float32) / 255.0
    lin = np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
    return 0.0722 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.2126 * lin[..., 2]


def _contrast(crop: np.ndarray) -> float:
    lum = _rel_lum(crop).reshape(-1)
    t = float(np.median(lum))
    for _ in range(8):
        hi, lo = lum[lum > t], lum[lum <= t]
        if len(hi) == 0 or len(lo) == 0:
            break
        t = float((hi.mean() + lo.mean()) / 2)
    hi = lum[lum > t]
    lo = lum[lum <= t]
    if len(hi) == 0 or len(lo) == 0:
        return 1.0
    return float((hi.mean() + 0.05) / (lo.mean() + 0.05))


def _whole(path: str, t: float, out: Path) -> str | None:
    f = grab(path, t, 720)
    if f is None:
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), label_frame(f, fmt_t(t)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    return str(out)


def counter_check(path: str, probe, text: dict, ev: Path) -> list[dict]:
    covers = "8 numbers that jiggle while they count"
    if not text["engine"]:
        return [not_run("counter_jiggle", covers, "No OCR engine.")]
    cands = []
    for tr in text["tracks"]:
        vals = [(_digits(r[1]), r[0]) for r in tr["readings"] if _digits(r[1])]
        distinct = {v for v, _ in vals}
        if len(distinct) >= 3 and len(vals) >= 3:
            cands.append((tr, vals))
    if not cands:
        return [check("counter_jiggle", covers, "info", {"counters_found": 0}, note="No number on screen changes its value.")]

    scale = probe.width / text["ocr_width"]
    events, rows = [], []
    for idx, (tr, vals) in enumerate(cands[:6]):
        boxes = np.array([b for _, b in tr["boxes"]], float) * scale
        x0, y0 = boxes[:, 0].min(), boxes[:, 1].min()
        x1, y1 = (boxes[:, 0] + boxes[:, 2]).max(), (boxes[:, 1] + boxes[:, 3]).max()
        pad = 0.35 * (y1 - y0)
        x0, x1 = int(max(x0 - pad, 0)), int(min(x1 + pad, probe.width))
        y0, y1 = int(max(y0 - pad, 0)), int(min(y1 + pad, probe.height))
        m = _jiggle_metrics(_crop_frames(path, tr["t0"], tr["t_last"], (x0, y0, x1, y1)))
        if m is None:
            continue
        backward = _backward(vals)
        row = {"t": round(tr["t0"], 2), "t_end": round(tr["t_last"], 2), "values_seen": sorted({v for v, _ in vals}, key=len)[:12],
               "box": [x0, y0, x1, y1], "backward_steps": backward, **m}
        rows.append(row)
        jig = max(m.get("column_jitter_pct") or 0.0, m.get("baseline_jitter_pct") or 0.0)
        if jig > th("counter_jitter_pct") or backward:
            e = dict(row)
            ts = np.linspace(tr["t0"], tr["t_last"], 6)
            frames = []
            for t in ts:
                f = grab(path, float(t))
                if f is not None:
                    frames.append(label_frame(cv2.resize(f[y0:y1, x0:x1], (420, int(420 * (y1 - y0) / max(x1 - x0, 1)))), fmt_t(float(t))))
            if frames:
                out_p = ev / f"counter_{idx}.jpg"
                out_p.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(out_p), cv2.vconcat(frames), [cv2.IMWRITE_JPEG_QUALITY, 92])
                e["evidence"] = str(out_p)
            events.append(e)
    return [check("counter_jiggle", covers, "flagged" if events else "clear", {"counters_found": len(rows), "counters": rows}, events,
                  ["counter_jitter_pct"])]


def _backward(vals: list[tuple[str, float]]) -> int:
    nums = [int(v) for v, _ in vals if len(v) <= 12]
    if len(nums) < 4:
        return 0
    rising = nums[-1] >= nums[0]
    steps = 0
    for a, b in zip(nums, nums[1:]):
        if (rising and b < a) or (not rising and b > a):
            if len(str(a)) == len(str(b)):
                steps += 1
    return steps


def _crop_frames(path: str, t0: float, t1: float, roi) -> np.ndarray:
    import subprocess
    x0, y0, x1, y1 = roi
    w, h = x1 - x0, y1 - y0
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{max(t0, 0):.3f}", "-t", f"{t1 - t0 + 0.2:.3f}", "-i", path, "-vf",
           f"crop={w}:{h}:{x0}:{y0},format=gray", "-fps_mode", "passthrough", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (w * h) if w * h else 0
    return np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w) if n else np.zeros((0, h, w), np.uint8)


def _glyph_boxes(g: np.ndarray) -> list[tuple[int, int, int, int]]:
    _, b = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if (b[np.r_[0, -1], :].mean() + b[:, np.r_[0, -1]].mean()) / 2 > 127:
        b = 255 - b
    count, _, stats, _ = cv2.connectedComponentsWithStats(b, 8)
    h, w = g.shape
    boxes = []
    for i in range(1, count):
        x, y, ww, hh, area = stats[i]
        if hh >= 0.3 * h and ww >= 2 and area >= 8 and x > 0 and y > 0 and x + ww < w and y + hh < h:
            boxes.append((int(x), int(y), int(ww), int(hh)))
    boxes.sort()
    if boxes:
        top = max(bx[3] for bx in boxes)
        boxes = [bx for bx in boxes if bx[3] >= 0.6 * top]
    return boxes


def _subpixel_shift(prev: np.ndarray, cur: np.ndarray, box, search: int) -> tuple[float, float, float]:
    """Find a glyph from the last frame in this one. Returns dx, dy and the match score."""
    x, y, w, h = box
    H, W = prev.shape
    tpl = prev[max(y, 0):y + h, max(x, 0):x + w]
    x0, y0 = max(x - search, 0), max(y - search, 0)
    win = cur[y0:min(y + h + search, H), x0:min(x + w + search, W)]
    if tpl.size == 0 or win.shape[0] < tpl.shape[0] or win.shape[1] < tpl.shape[1] or tpl.std() < 3:
        return 0.0, 0.0, 0.0
    res = cv2.matchTemplate(win, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    px, py = loc

    def refine(v: float, a: float, b: float) -> float:
        d = a - 2 * v + b
        return 0.0 if abs(d) < 1e-6 else 0.5 * (a - b) / d
    fx = refine(res[py, px], res[py, px - 1], res[py, px + 1]) if 0 < px < res.shape[1] - 1 else 0.0
    fy = refine(res[py, px], res[py - 1, px], res[py + 1, px]) if 0 < py < res.shape[0] - 1 else 0.0
    return px + fx + x0 - x, py + fy + y0 - y, float(score)


def _jiggle_metrics(frames: np.ndarray) -> dict | None:
    """A digit that keeps its value should not move while its neighbours count.
    Track each glyph while it matches itself. Slow slides are removed, only the shake remains."""
    if len(frames) < 8:
        return None
    n_boxes = [len(_glyph_boxes(f)) for f in frames]
    mode = Counter(n_boxes).most_common(1)[0][0]
    if mode == 0:
        return None
    start = n_boxes.index(mode)
    boxes = _glyph_boxes(frames[start])
    digit_h = float(np.median([b[3] for b in boxes]))
    search = max(4, int(digit_h * 0.25))
    cols = []
    for box in boxes:
        pad = 2
        box = (box[0] - pad, box[1] - pad, box[2] + 2 * pad, box[3] + 2 * pad)
        dxs, dys, holds = [], [], 0
        pos = list(box)
        for i in range(start + 1, len(frames)):
            dx, dy, score = _subpixel_shift(frames[i - 1], frames[i], tuple(int(round(v)) for v in pos), search)
            if score >= th("counter_match"):
                dxs.append(dx)
                dys.append(dy)
                pos[0] += dx
                pos[1] += dy
                holds += 1
            else:
                dxs.append(np.nan)
                dys.append(np.nan)
        cols.append({"held_share": holds / max(len(frames) - start - 1, 1), "dx": np.array(dxs), "dy": np.array(dys)})
    held = [c for c in cols if c["held_share"] >= 0.25]
    if not held:
        return {"frames_measured": len(frames), "digit_height_px": round(digit_h, 1), "glyphs": len(boxes), "held_digits": 0, "column_jitter_pct": None, "baseline_jitter_pct": None}

    def shake(v: np.ndarray) -> float:
        v = v[~np.isnan(v)]
        return float(np.std(v - np.median(v))) if len(v) >= 4 else 0.0
    sx = float(np.median([shake(c["dx"]) for c in held]))
    sy = float(np.median([shake(c["dy"]) for c in held]))
    return {"frames_measured": len(frames), "digit_height_px": round(digit_h, 1), "glyphs": len(boxes), "held_digits": len(held),
            "column_jitter_px": round(sx, 2), "column_jitter_pct": round(sx / max(digit_h, 1) * 100, 2),
            "baseline_jitter_px": round(sy, 2), "baseline_jitter_pct": round(sy / max(digit_h, 1) * 100, 2)}
