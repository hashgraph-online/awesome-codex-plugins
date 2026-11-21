"""Items 4, 5, 6: why anything moves, what is stuck to the glass, what slides off its target."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from mj_common import check, fmt_t, grab, label_frame, read_frames, strip, th

W = 480


def load_gray(path: str) -> np.ndarray:
    frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in read_frames(path, W)]
    return np.stack(frames) if frames else np.zeros((0, 2, 2), np.uint8)


def camera_track(gray: np.ndarray, shots: list[dict]) -> dict:
    """Per-frame camera estimate. A global affine fit on tracked corners, the rest counts as object motion."""
    n = len(gray)
    tx, ty, sc, rot, resid, inl = (np.zeros(n) for _ in range(6))
    transforms = np.tile(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]), (n, 1, 1))
    firsts = {s["first_frame"] for s in shots}
    lk = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 20, 0.03))
    for i in range(1, n):
        if i in firsts:
            continue
        a, b = gray[i - 1], gray[i]
        pts = cv2.goodFeaturesToTrack(a, 300, 0.01, 8)
        if pts is None or len(pts) < 12:
            resid[i] = float(cv2.absdiff(a, b).mean())
            continue
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(a, b, pts, None, **lk)
        good = st.ravel() == 1
        p0, p1 = pts[good], nxt[good]
        if len(p0) < 8:
            resid[i] = float(cv2.absdiff(a, b).mean())
            continue
        M, inliers = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=1.0, maxIters=200)
        if M is None:
            resid[i] = float(cv2.absdiff(a, b).mean())
            continue
        transforms[i] = M
        s = float(np.hypot(M[0, 0], M[1, 0]))
        tx[i], ty[i], sc[i], rot[i] = M[0, 2], M[1, 2], s - 1.0, float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
        inl[i] = float(inliers.mean())
        warped = cv2.warpAffine(a, M, (a.shape[1], a.shape[0]))
        d = cv2.absdiff(warped, b)
        resid[i] = float(d[8:-8, 8:-8].mean())
    h, w = gray.shape[1:]
    speed = np.hypot(tx, ty) + np.abs(sc) * np.hypot(w, h) / 2
    return {"tx": tx, "ty": ty, "scale": sc, "rot": rot, "resid": resid, "inlier": inl, "speed": speed, "transforms": transforms}


def expected_travel(cam: dict, a: int, b: int, x: float, y: float) -> float:
    """How far the camera path says this point should have gone. The centre of a push-in stays put."""
    p = np.array([x, y, 1.0])
    start, far = p[:2].copy(), 0.0
    for i in range(a + 1, b + 1):
        p[:2] = cam["transforms"][i] @ p
        far = max(far, float(np.hypot(*(p[:2] - start))))
    return far


def describe_shot(cam: dict, s: dict, fps: float) -> dict:
    a, b = s["first_frame"] + 1, s["last_frame"] + 1
    if b - a < 3:
        return {"camera": "too short", "speed_pct_per_s": 0.0}
    tx, ty, sc = cam["tx"][a:b], cam["ty"][a:b], cam["scale"][a:b]
    px_s = float(np.median(cam["speed"][a:b])) * fps
    pct = px_s / W * 100
    mx, my, ms = float(np.mean(tx)) * fps, float(np.mean(ty)) * fps, float(np.mean(sc)) * fps * 100
    # high-pass of the path: shake that is not a move
    path = np.cumsum(np.c_[tx, ty], axis=0)
    k = max(3, int(fps / 2)) | 1
    smooth = np.c_[np.convolve(path[:, 0], np.ones(k) / k, "same"), np.convolve(path[:, 1], np.ones(k) / k, "same")]
    shake = float(np.sqrt(((path - smooth)[k:-k] ** 2).sum(axis=1).mean())) if len(path) > 2 * k + 2 else 0.0
    kind = "locked"
    if pct > th("camera_move_pct_s"):
        if abs(ms) * W / 100 / 2 > max(abs(mx), abs(my)):
            kind = "push in" if ms > 0 else "pull out"
        elif abs(mx) > abs(my):
            kind = "pan right" if mx < 0 else "pan left"
        else:
            kind = "tilt down" if my < 0 else "tilt up"
    sp = cam["speed"][a:b]
    cv = float(np.std(sp) / max(np.mean(sp), 1e-6))
    return {"camera": kind, "speed_pct_per_s": round(pct, 2), "shake_px": round(shake, 2), "speed_cv": round(cv, 2),
            "object_motion": round(float(np.median(cam["resid"][a:b])), 2)}


def motion_cause_check(path: str, cam: dict, shots: list[dict], t: np.ndarray, onsets: np.ndarray | None, text: dict, ev: Path) -> list[dict]:
    covers = "4 motion has no cause"
    n = len(t)
    if n < 10:
        return []
    fps = 1 / float(np.median(np.diff(t)))
    text_times = []
    for tr in text.get("tracks", []):
        if len(tr["readings"]) >= 2:  # A word read once is often OCR noise, not a change on screen.
            text_times += [tr["t0"], tr["t_last"]]
    text_times = np.array(sorted(text_times)) if text_times else np.zeros(0)
    onsets_a = np.array(onsets) if onsets is not None else np.zeros(0)
    events, all_onsets = [], []
    lo_len = max(4, int(0.3 * fps))
    hi_len = 4
    channels = [("object", cam["resid"], th("object_jump")), ("camera", cam["speed"], th("camera_jump"))]
    for s in shots:
        a, b = s["first_frame"] + 3, s["last_frame"]
        if b - a < lo_len + hi_len + 1:
            continue
        for kind, sig, floor in channels:
            i = a + lo_len
            while i < b - hi_len:
                base = float(np.median(sig[i - lo_len:i]))
                after = float(np.median(sig[i + 1:i + 1 + hi_len]))
                # A start is a rise above what this shot was already doing.
                if after - base > max(floor, th("motion_ratio") * base):
                    tm = float(t[i])
                    near_sound = bool(len(onsets_a) and np.min(np.abs(onsets_a - tm)) <= th("cause_window_s"))
                    near_text = bool(len(text_times) and np.min(np.abs(text_times - tm)) <= 0.6)  # OCR samples at 2 fps
                    row = {"t": round(tm, 3), "shot": s["index"], "kind": kind, "rise": round(after - base, 2), "from": round(base, 2),
                           "sound_within_window": near_sound, "text_change_near": near_text}
                    all_onsets.append(row)
                    if not near_sound and not near_text:
                        r = dict(row)
                        r["evidence"] = strip(path, [float(t[max(i - 4, 0)]), tm, float(t[min(i + 4, n - 1)])], ev / f"motion_{i}.jpg", width=400)
                        events.append(r)
                    i += int(fps)
                i += 1
    desc = [dict(shot=s["index"], t=s["start"], **describe_shot(cam, s, fps)) for s in shots]
    moved = [d for d in desc if d["camera"] in {"push in", "pull out", "pan left", "pan right", "tilt up", "tilt down"}]
    drifting = [d for d in moved if d.get("speed_cv", 9) < th("drift_cv") and d["speed_pct_per_s"] < th("drift_max_pct_s")]
    long_enough = [d for d in desc if d["camera"] != "too short"]
    drift_share = len(drifting) / max(len(long_enough), 1)
    return [
        check("motion_cause", covers, "flagged" if events else ("clear" if all_onsets else "info"),
              {"moves_started": len(all_onsets), "moves_with_nothing_near": len(events), "moves": all_onsets[:30]}, events[:12],
              ["object_jump", "camera_jump", "motion_ratio", "cause_window_s"],
              note="No sound and no text change near a move does not prove no cause. Open the strip and name the cause in the picture or report that there is none."),
        check("constant_drift", covers, "flagged" if drift_share >= th("drift_share") and len(long_enough) >= 3 else "clear",
              {"shots": len(long_enough), "constant_drift_shots": len(drifting), "share": round(drift_share, 3), "per_shot": desc},
              [{"t": d["t"], "shot": d["shot"], "camera": d["camera"], "speed_pct_per_s": d["speed_pct_per_s"], "speed_cv": d["speed_cv"]} for d in drifting[:10]],
              ["drift_share", "drift_cv"], note="Every shot slowly moving at a constant speed is how a move with no reason looks in numbers."),
        check("camera_shake", "4 motion has no cause",
              "flagged" if any(d.get("shake_px", 0) > th("shake_px") for d in desc) else "clear",
              {"worst_shake_px": max((d.get("shake_px", 0) for d in desc), default=0)},
              [{"t": d["t"], "shot": d["shot"], "shake_px": d["shake_px"]} for d in desc if d.get("shake_px", 0) > th("shake_px")][:10], ["shake_px"]),
    ]


def pinned_check(path: str, gray: np.ndarray, cam: dict, shots: list[dict], t: np.ndarray, text: dict, fps: float, ev: Path) -> tuple[list[dict], list[dict]]:
    """Regions that stay still on the glass while the picture around them moves."""
    covers = "5 graphics are pinned to the screen"
    regions, tested = [], 0
    H, Wd = gray.shape[1:]
    for s in shots:
        a, b = s["first_frame"], s["last_frame"]
        if b - a < max(8, 0.4 * fps):
            continue
        idx = np.linspace(a, b, min(40, b - a + 1)).astype(int)
        st = gray[idx].astype(np.float32)
        # Inter-decile spread, scaled to a std. One glitch frame cannot fake a moving scene.
        tstd = (np.percentile(st, 90, axis=0) - np.percentile(st, 10, axis=0)) / 2.56
        mean = st.mean(axis=0)
        cam_speed = float(np.median(cam["speed"][a + 1:b + 1])) * fps / Wd * 100
        scene_moves = float(np.percentile(tstd, 60))
        if scene_moves < th("pinned_scene_std"):
            continue
        tested += 1
        lap = np.abs(cv2.Laplacian(mean, cv2.CV_32F))
        lap = cv2.GaussianBlur(lap, (0, 0), 3)
        still = (tstd < th("pinned_still_std")) & (lap > th("pinned_detail"))
        # Bars in a letterbox hold still by design. Mask them and the edge they make with the picture.
        bright = st.max(axis=0)
        bar_rows = np.where(np.percentile(bright, 90, axis=1) < 24)[0]
        bar_cols = np.where(np.percentile(bright, 90, axis=0) < 24)[0]
        if len(bar_rows):
            still[np.clip(np.r_[bar_rows, bar_rows + 4, bar_rows - 4, bar_rows + 8, bar_rows - 8], 0, H - 1), :] = False
        if len(bar_cols):
            still[:, np.clip(np.r_[bar_cols, bar_cols + 4, bar_cols - 4, bar_cols + 8, bar_cols - 8], 0, Wd - 1)] = False
        mask = cv2.morphologyEx(still.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        for i in range(1, n):
            x, y, w, h, area = stats[i]
            frac = area / (Wd * H)
            if frac < 0.0015 or frac > 0.35 or w >= 0.97 * Wd:
                continue
            ring = cv2.dilate((labels == i).astype(np.uint8), np.ones((31, 31), np.uint8)).astype(bool) & ~(labels == i)
            ring_std = float(tstd[ring].mean()) if ring.any() else 0.0
            # Median, because closing the mask pulls in the moving gaps between letters.
            inner_std = float(np.median(tstd[labels == i]))
            if ring_std < th("pinned_ring_ratio") * max(inner_std, 0.5):
                continue
            # A graphic has crisper edges than the footage it sits on.
            crisp = float(lap[labels == i].mean()) / max(float(np.median(lap)), 0.5)
            # If the camera says this spot should not have moved, stillness proves nothing.
            travel = expected_travel(cam, a, b, x + w / 2, y + h / 2) / Wd * 100
            if travel < th("pinned_min_travel_pct"):
                continue
            # A real overlay looks the same in every frame. A label passing over a smooth patch does not.
            crop_mean = mean[y:y + h, x:x + w]
            persist = float(np.median([cv2.matchTemplate(fr[y:y + h, x:x + w], crop_mean, cv2.TM_CCOEFF_NORMED)[0, 0] for fr in st]))
            if persist < th("pinned_persist"):
                continue
            nx, ny, nw, nh = x / Wd, y / H, w / Wd, h / H
            words, words_w = _text_in(text, s, (nx, ny, nw, nh))
            lower_third = ny > 0.68 or ny + nh < 0.2
            wide = words_w >= 0.33
            kind = "caption or title" if (words and (wide or (lower_third and nw > 0.15))) else ("text label" if words else "graphic")
            if kind == "graphic" and crisp < th("pinned_crisp"):
                continue
            regions.append({"shot": s["index"], "t": s["start"], "t_end": s["end"], "box": [round(nx, 3), round(ny, 3), round(nw, 3), round(nh, 3)],
                            "inner_motion": round(inner_std, 2), "scene_motion": round(ring_std, 2), "camera_speed_pct_s": round(cam_speed, 2), "camera_should_have_moved_it_pct": round(travel, 1), "same_in_every_frame": round(persist, 2),
                            "kind": kind, "text": words[:60]})
    flagged = [r for r in regions if r["kind"] != "caption or title"]
    events = []
    for k, r in enumerate(flagged[:8]):
        f = grab(path, (r["t"] + r["t_end"]) / 2, 720)
        if f is None:
            continue
        hh, ww = f.shape[:2]
        x, y, w, h = int(r["box"][0] * ww), int(r["box"][1] * hh), int(r["box"][2] * ww), int(r["box"][3] * hh)
        cv2.rectangle(f, (x, y), (x + w, y + h), (0, 255, 255), 2)
        p = ev / f"pinned_{k}.jpg"
        p.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(p), label_frame(f, f"{fmt_t(r['t'])} stuck to the glass"), [cv2.IMWRITE_JPEG_QUALITY, 88])
        e = dict(r)
        e["evidence"] = str(p)
        events.append(e)
    res = [check("pinned_graphics", covers, "flagged" if flagged else ("clear" if tested else "info"),
                 {"shots_tested": tested, "regions": len(regions), "graphics_stuck": len(flagged), "captions_stuck": len(regions) - len(flagged)},
                 events, ["pinned_still_std", "pinned_scene_std"],
                 note="A caption or a logo bug on the glass is fine. A label or a graphic that claims to belong to the scene is not. Testable only in shots where the scene moves.")]
    return res, regions


def _text_in(text: dict, s: dict, box) -> tuple[str, float]:
    """Text that overlaps a region, and how wide that text is as a share of the frame."""
    if not text.get("tracks"):
        return "", 0.0
    W_, H_ = text["ocr_width"], text["ocr_height"]
    bx, by, bw, bh = box
    out, widest = [], 0.0
    for tr in text["tracks"]:
        if tr["t_last"] < s["start"] or tr["t0"] > s["end"]:
            continue
        x, y, w, h = tr["box"]
        x0, y0, x1, y1 = x / W_, y / H_, (x + w) / W_, (y + h) / H_
        if min(x1, bx + bw) - max(x0, bx) > 0 and min(y1, by + bh) - max(y0, by) > 0:
            out.append(tr["last"])
            widest = max(widest, x1 - x0)
    return " ".join(out), widest


def _lk_step(a, b, pts):
    if pts is None or len(pts) == 0:
        return None, None
    lk = dict(winSize=(15, 15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 15, 0.03))
    nxt, st, _ = cv2.calcOpticalFlowPyrLK(a, b, pts, None, **lk)
    good = st.ravel() == 1
    return pts[good], nxt[good]


def label_drift_check(path: str, gray: np.ndarray, t: np.ndarray, shots: list[dict], text: dict, labels: list[dict] | None, ev: Path) -> list[dict]:
    """Track a label and the patch of world around it. If they part, the label has slid off."""
    covers = "6 labels slide off what they point at"
    H, Wd = gray.shape[1:]
    jobs = []
    if labels:
        for l in labels:
            jobs.append({"t0": l["t0"], "t1": l["t1"], "box": l["label_box"], "anchor": l.get("anchor_box"), "text": l.get("text", ""), "source": "manifest"})
    elif text.get("tracks"):
        kx, ky = Wd / text["ocr_width"], H / text["ocr_height"]
        for tr in text["tracks"]:
            if tr["t_last"] - tr["t0"] < 0.5:
                continue
            x, y, w, h = tr["boxes"][0][1]
            ny = y / text["ocr_height"]
            if (ny > 0.68 or ny < 0.12) and w / text["ocr_width"] > 0.2:
                continue  # captions and titles do not point at anything
            jobs.append({"t0": tr["t0"], "t1": tr["t_last"], "box": [x * kx, y * ky, w * kx, h * ky], "anchor": None, "text": tr["last"], "source": "ocr"})
    if not jobs:
        return [check("label_drift", covers, "info", {"labels_tracked": 0}, note="No label to track. Pass --labels with the render's anchors for an exact test.")]
    rows, events = [], []
    for j, job in enumerate(jobs[:20]):
        f0 = int(np.searchsorted(t, job["t0"]))
        f1 = min(int(np.searchsorted(t, job["t1"])), len(gray) - 1)
        # stay inside the shot
        s = next((s for s in shots if s["first_frame"] <= f0 <= s["last_frame"]), None)
        if s is None:
            continue
        f1 = min(f1, s["last_frame"])
        if f1 - f0 < 4:
            continue
        x, y, w, h = [float(v) for v in job["box"]]
        lmask = np.zeros((H, Wd), np.uint8)
        lmask[max(int(y), 0):int(y + h), max(int(x), 0):int(x + w)] = 255
        if job["anchor"]:
            ax, ay, aw, ah = [float(v) for v in job["anchor"]]
            amask = np.zeros((H, Wd), np.uint8)
            amask[max(int(ay), 0):int(ay + ah), max(int(ax), 0):int(ax + aw)] = 255
        else:
            grow = int(max(h * 2.2, 14))
            amask = np.zeros((H, Wd), np.uint8)
            amask[max(int(y) - grow, 0):int(y + h) + grow, max(int(x) - grow, 0):int(x + w) + grow] = 255
            amask[lmask > 0] = 0
        lpts = cv2.goodFeaturesToTrack(gray[f0], 40, 0.01, 3, mask=lmask)
        apts = cv2.goodFeaturesToTrack(gray[f0], 80, 0.01, 5, mask=amask)
        if apts is None or len(apts) < 5:
            continue
        rel = np.zeros(2)
        rel_path = []
        lost = 0
        for i in range(f0, f1):
            a, b = gray[i], gray[i + 1]
            p0, p1 = _lk_step(a, b, apts)
            if p0 is None or len(p0) < 3:
                lost += 1
                break
            am = np.median(p1 - p0, axis=0)
            apts = p1.reshape(-1, 1, 2)
            lm = np.zeros(2)
            if lpts is not None and len(lpts):
                q0, q1 = _lk_step(a, b, lpts)
                if q0 is not None and len(q0) >= 2:
                    lm = np.median(q1 - q0, axis=0)
                    lpts = q1.reshape(-1, 1, 2)
            rel += (am - lm).reshape(2)
            rel_path.append(float(np.hypot(*rel)))
        if not rel_path:
            continue
        peak = max(rel_path) / Wd * 100
        row = {"t": round(job["t0"], 2), "t_end": round(job["t1"], 2), "text": job["text"][:60], "source": job["source"], "peak_drift_pct_width": round(peak, 2),
               "frames_tracked": len(rel_path)}
        rows.append(row)
        if peak > th("label_drift_pct"):
            e = dict(row)
            e["evidence"] = strip(path, [float(t[f0]), float(t[(f0 + f1) // 2]), float(t[f1])], ev / f"label_{j}.jpg", width=480)
            events.append(e)
    if not rows:
        return [check("label_drift", covers, "info", {"labels_tracked": 0}, note="Nothing around the labels had texture to track. Pass --labels for an exact test.")]
    return [check("label_drift", covers, "flagged" if events else "clear", {"labels_tracked": len(rows), "labels": rows}, events[:10], ["label_drift_pct"],
                  note="Without --labels the world around a label stands in for its target, so a floating label over a moving scene also shows drift. Open the strip.")]
