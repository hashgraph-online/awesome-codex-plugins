"""Frame facts: shots, black, frozen, repeated, glitch frames, flicker, flashes."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from mj_common import check, fmt_t, read_frames, strip, th

PROXY_W = 320
GRID = 8


@dataclass
class FrameTrace:
    t: np.ndarray = field(default_factory=lambda: np.zeros(0))
    luma: np.ndarray = field(default_factory=lambda: np.zeros(0))
    luma_std: np.ndarray = field(default_factory=lambda: np.zeros(0))
    rel_lum: np.ndarray = field(default_factory=lambda: np.zeros(0))
    mad: np.ndarray = field(default_factory=lambda: np.zeros(0))
    cell_max: np.ndarray = field(default_factory=lambda: np.zeros(0))
    hsv_delta: np.ndarray = field(default_factory=lambda: np.zeros(0))
    skip2: np.ndarray = field(default_factory=lambda: np.zeros(0))
    cell_luma: np.ndarray = field(default_factory=lambda: np.zeros(0))
    luma_p99: np.ndarray = field(default_factory=lambda: np.zeros(0))


def trace(path: str, pts: list[float], v_start: float = 0.0) -> FrameTrace:
    """One pass over every coded frame. Only numbers are kept."""
    luma, std, rel, mad, cmax, hd, sk2, cells, p99 = [], [], [], [], [], [], [], [], []
    prev, prev2, prev_hsv = None, None, None
    for f in read_frames(path, PROXY_W):
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV).astype(np.float32)
        luma.append(float(g.mean()))
        std.append(float(g.std()))
        p99.append(float(np.percentile(g, 99)))
        # WCAG relative luminance on the small frame, used for the flash test
        lin = ((f.astype(np.float32) / 255.0) ** 2.2)
        rel.append(float((0.0722 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.2126 * lin[..., 2]).mean()))
        c = cv2.resize(g, (GRID, GRID), interpolation=cv2.INTER_AREA)
        cells.append(c)
        if prev is None:
            mad.append(0.0); cmax.append(0.0); hd.append(0.0); sk2.append(0.0)
        else:
            d = np.abs(g - prev)
            mad.append(float(d.mean()))
            cmax.append(float(cv2.resize(d, (GRID, GRID), interpolation=cv2.INTER_AREA).max()))
            # hue wraps at 180 in OpenCV
            dh = np.abs(hsv[..., 0] - prev_hsv[..., 0])
            dh = np.minimum(dh, 180 - dh)
            hd.append(float((dh.mean() + np.abs(hsv[..., 1] - prev_hsv[..., 1]).mean()
                             + np.abs(hsv[..., 2] - prev_hsv[..., 2]).mean()) / 3))
            sk2.append(float(np.abs(g - prev2).mean()) if prev2 is not None else 0.0)
        prev2, prev, prev_hsv = prev, g, hsv
    n = len(luma)
    t = np.array(pts[:n], float) - v_start if len(pts) >= n else np.arange(n) / 30.0
    return FrameTrace(t, np.array(luma), np.array(std), np.array(rel), np.array(mad), np.array(cmax),
                      np.array(hd), np.array(sk2), np.array(cells), np.array(p99))


def detect_shots(tr: FrameTrace) -> list[dict]:
    """Cuts are frames whose colour change stands far above the shot around them."""
    n = len(tr.t)
    if n == 0:
        return []
    cuts = []
    base = th("cut_hsv_delta")
    for i in range(1, n):
        v = tr.hsv_delta[i]
        lo, hi = max(1, i - 8), min(n, i + 9)
        around = np.r_[tr.hsv_delta[lo:i], tr.hsv_delta[i + 1:hi]]
        local = float(np.median(around)) if len(around) else 0.0
        if v > base and v > 3.5 * max(local, 1.0):
            cuts.append(i)
    # One frame outliers come back to the old picture. They are glitches, not cuts.
    keep = []
    for i in cuts:
        if i + 1 < n and tr.skip2[i + 1] < 0.35 * min(tr.mad[i], tr.mad[i + 1] + 1e-6):
            continue
        if i + 2 < n and tr.mad[i + 1] > 0 and i - 1 >= 0 and i + 1 in cuts:
            # two adjacent cut frames, keep the first and let the short shot check see it
            pass
        keep.append(i)
    keep = _merge_ramps(keep, tr.luma)
    shots = []
    start = 0
    for c in keep + [n]:
        if c > start:
            end_t = float(tr.t[c]) if c < n else float(tr.t[-1] + (tr.t[-1] - tr.t[-2] if n > 1 else 0))
            shots.append({"index": len(shots), "start": round(float(tr.t[start]), 3), "end": round(end_t, 3),
                          "duration": round(end_t - float(tr.t[start]), 3), "first_frame": start, "last_frame": c - 1})
        start = c
    return shots


def _merge_ramps(cuts: list[int], luma: np.ndarray) -> list[int]:
    """Adjacent cut frames where brightness only climbs or only falls are one flash or fade. Keep its last frame."""
    out, i = [], 0
    while i < len(cuts):
        j = i
        while j + 1 < len(cuts) and cuts[j + 1] - cuts[j] <= 1:
            j += 1
        if j > i:
            seg = np.diff(luma[cuts[i] - 1:cuts[j] + 1])
            # A flash climbs and then lands on the next shot, so the last step can go either way.
            core = seg[:-1] if len(seg) >= 3 else seg
            if np.all(core >= -0.5) or np.all(core <= 0.5):
                out.append(cuts[j])
                i = j + 1
                continue
        out.extend(cuts[i:j + 1])
        i = j + 1
    return out


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def frame_checks(path: str, tr: FrameTrace, shots: list[dict], decode_errors: list, ev: Path) -> list[dict]:
    res = []
    n = len(tr.t)
    if n < 3:
        return res
    dt = float(np.median(np.diff(tr.t)))
    fps = 1.0 / dt if dt else 30.0
    cut_frames = {s["first_frame"] for s in shots}

    res.append(check("decode_errors", "broken frames", "flagged" if decode_errors else "clear",
                     {"count": len(decode_errors), "first": decode_errors[:3]}))

    # black frames: a fade into black is fine, a black frame out of nowhere is a seam error
    # A dim terminal is dark and flat too, but something is on screen, so look at the brightest pixels as well.
    black = (tr.luma < th("black_luma")) & (tr.luma_std < th("black_std")) & (tr.luma_p99 < th("black_p99"))
    events, intentional = [], []
    for a, b in _runs(black):
        dur = float(tr.t[b] - tr.t[a] + dt)
        before = tr.luma[a - 1] if a > 0 else 0.0
        after = tr.luma[b + 1] if b + 1 < n else 0.0
        at_edge = a <= 1 or b >= n - 2
        abrupt = (before > 2 * th("black_luma") or after > 2 * th("black_luma"))
        short = dur <= th("black_glitch_max_s")
        e = {"t": round(float(tr.t[a]), 3), "t_end": round(float(tr.t[b]) + dt, 3), "frames": int(b - a + 1),
             "duration_s": round(dur, 3), "abrupt": bool(abrupt)}
        if not at_edge and short and abrupt:
            times = [float(tr.t[max(a - 1, 0)]), float(tr.t[a]), float(tr.t[min(b + 1, n - 1)])]
            e["evidence"] = strip(path, times, ev / f"black_{a}.jpg")
            events.append(e)
        else:
            intentional.append(e)
    res.append(check("black_frames", "broken frames", "flagged" if events else "clear",
                     {"glitch_count": len(events), "other_black_runs": intentional,
                      "black_share": round(float(black.mean()), 4)}, events, ["black_luma", "black_std", "black_glitch_max_s"]))

    # frozen: no pixel moves, while the picture moved before and after
    still = tr.mad < th("freeze_mad")
    still[0] = False
    events, holds = [], []
    moving_level = th("freeze_motion_around")
    w = max(3, int(fps / 2))
    for a, b in _runs(still):
        dur = float(tr.t[b] - tr.t[a] + dt)
        if dur < th("freeze_min_s"):
            continue
        before = float(np.median(tr.mad[max(1, a - w):a])) if a > 1 else 0.0
        after = float(np.median(tr.mad[b + 1:b + 1 + w])) if b + 1 < n else 0.0
        e = {"t": round(float(tr.t[a]), 3), "t_end": round(float(tr.t[b]) + dt, 3), "duration_s": round(dur, 3),
             "motion_before": round(before, 3), "motion_after": round(after, 3)}
        ends_video = b >= n - 2
        if before > moving_level and (after > moving_level or ends_video):
            e["kind"] = "frozen tail" if ends_video else "frozen mid-action"
            e["evidence"] = strip(path, [float(tr.t[max(a - 2, 0)]), float(tr.t[a]), float(tr.t[b]), float(tr.t[min(b + 1, n - 1)])],
                                  ev / f"freeze_{a}.jpg")
            events.append(e)
        else:
            holds.append(e)
    res.append(check("frozen_frames", "broken frames", "flagged" if events else "clear",
                     {"frozen_count": len(events), "still_holds": holds, "still_share": round(float(still.mean()), 4)},
                     events, ["freeze_mad", "freeze_min_s"]))

    # repeated frames inside motion: a stutter the eye sees and a sampled review misses
    rep, i = [], 2
    while i < n - 2:
        if i not in cut_frames:
            around = float(np.median([tr.mad[i - 1], tr.mad[i + 1], tr.mad[i + 2]]))
            # An encoder never makes a repeat quite identical, so judge it against the motion around it.
            if around > th("repeat_motion_around") and tr.mad[i] < max(th("repeat_mad"), th("repeat_ratio") * around):
                rep.append(i)
        i += 1
    moving = int((tr.mad[1:] > th("repeat_motion_around")).sum())
    share = len(rep) / max(moving, 1)
    rep_events = [{"t": round(float(tr.t[i]), 3), "mad": round(float(tr.mad[i]), 3)} for i in rep[:40]]
    if rep:
        i = rep[len(rep) // 2]
        rep_events[0]["evidence"] = strip(path, [float(tr.t[i - 1]), float(tr.t[i]), float(tr.t[i + 1])], ev / "repeat.jpg")
    res.append(check("repeated_frames", "broken frames",
                     "flagged" if share > th("repeat_share") else "clear",
                     {"count": len(rep), "share_of_moving_frames": round(share, 4)}, rep_events[:12], ["repeat_share"]))

    # glitch: frame i differs from both neighbours while the neighbours match each other
    glitch = []
    for i in range(1, n - 1):
        if i in cut_frames and (i + 1) in cut_frames:
            pass
        d_in, d_out, through = tr.mad[i], tr.mad[i + 1], tr.skip2[i + 1]
        cell_in, cell_out = tr.cell_max[i], tr.cell_max[i + 1]
        lo, hi = max(1, i - 12), min(n, i + 13)
        local = float(np.median(tr.mad[lo:hi]))
        local_cell = float(np.median(tr.cell_max[lo:hi]))
        whole = min(d_in, d_out) > max(th("glitch_min_mad"), 4 * local) and through < th("glitch_return") * min(d_in, d_out)
        part = (min(cell_in, cell_out) > max(th("glitch_min_cell"), 4 * local_cell)
                and through < 0.6 * max(d_in, d_out) and min(d_in, d_out) > 1.5 * through)
        if whole or part:
            glitch.append(i)
    # merge neighbours, keep the strongest of each cluster
    events, last = [], -10
    for i in glitch:
        if i - last > 1:
            e = {"t": round(float(tr.t[i]), 3), "frame": int(i), "jump_in": round(float(tr.mad[i]), 2),
                 "jump_out": round(float(tr.mad[i + 1]), 2), "neighbours_differ": round(float(tr.skip2[i + 1]), 2),
                 "max_cell_jump": round(float(max(tr.cell_max[i], tr.cell_max[i + 1])), 2)}
            e["evidence"] = strip(path, [float(tr.t[i - 1]), float(tr.t[i]), float(tr.t[i + 1])], ev / f"glitch_{i}.jpg")
            events.append(e)
        last = i
    res.append(check("glitch_frames", "broken frames", "flagged" if events else "clear", {"count": len(events)},
                     events[:15], ["glitch_min_mad", "glitch_return"]))

    # very short shots: a seam left behind by concatenation
    short = [s for s in shots if s["duration"] < th("seam_shot_s")]
    ev_short = [{"t": s["start"], "t_end": s["end"], "duration_s": s["duration"],
                 "evidence": strip(path, [max(s["start"] - dt, 0), s["start"], s["end"]], ev / f"seam_{s['index']}.jpg")}
                for s in short[:10]]
    res.append(check("seam_shots", "broken frames", "flagged" if short else "clear", {"count": len(short)},
                     ev_short, ["seam_shot_s"]))

    # flicker: luminance that shakes inside a shot, whole frame or local cells
    fl_events, per_shot = [], []
    for s in shots:
        a, b = s["first_frame"], s["last_frame"]
        if b - a < 8:
            continue
        sig = tr.luma[a:b + 1]
        d = np.diff(sig)
        flips = (np.sign(d[1:]) * np.sign(d[:-1]) < 0) & (np.minimum(np.abs(d[1:]), np.abs(d[:-1])) > th("flicker_step"))
        flip_rate = float(flips.sum()) / (len(flips) / fps)
        # local shimmer: cell luma high-pass in cells that do not otherwise move
        cells = tr.cell_luma[a:b + 1]
        hp = cells - cv2.blur(cells.astype(np.float32).reshape(len(cells), -1), (1, 5)).reshape(cells.shape)
        cell_rms = float(np.median(np.median(np.abs(hp), axis=0)) * 1.4826)
        per_shot.append({"shot": s["index"], "flip_rate_hz": round(flip_rate, 2), "cell_hf_rms": round(cell_rms, 3)})
        if flip_rate > th("flicker_flip_hz") or cell_rms > th("flicker_cell_rms"):
            mid = (a + b) // 2
            fl_events.append({"t": s["start"], "t_end": s["end"], "flip_rate_hz": round(flip_rate, 2),
                              "cell_hf_rms": round(cell_rms, 3),
                              "evidence": strip(path, [float(tr.t[mid + k]) for k in (0, 1, 2, 3) if mid + k <= b],
                                                ev / f"flicker_{s['index']}.jpg", width=320)})
    res.append(check("flicker", "broken frames", "flagged" if fl_events else "clear",
                     {"shots_flagged": len(fl_events), "per_shot": per_shot}, fl_events[:10],
                     ["flicker_flip_hz", "flicker_cell_rms"]))

    # flash safety: WCAG 2.3.1 general flash, at most three per second
    dl = tr.rel_lum
    transitions = []
    i, lo_i = 1, 0
    direction = 0
    ref = dl[0]
    for i in range(1, n):
        change = dl[i] - ref
        if abs(change) >= 0.10 and min(dl[i], ref) < 0.80:
            d = 1 if change > 0 else -1
            if direction == 0 or d != direction:
                transitions.append(i)
                direction = d
            ref = dl[i]
        elif direction and ((direction > 0 and dl[i] > ref) or (direction < 0 and dl[i] < ref)):
            ref = dl[i]
    flash_events, worst = [], 0.0
    tt = np.array(transitions, int)
    for a in range(0, len(tt)):
        window = tt[(tr.t[tt] >= tr.t[tt[a]]) & (tr.t[tt] < tr.t[tt[a]] + 1.0)]
        flashes = len(window) / 2.0
        worst = max(worst, flashes)
        if flashes > th("flash_per_s") and (not flash_events or tr.t[tt[a]] > flash_events[-1]["t"] + 1):
            flash_events.append({"t": round(float(tr.t[tt[a]]), 3), "flashes_in_1s": flashes})
    res.append(check("flash_safety", "broken frames", "flagged" if flash_events else "clear",
                     {"max_flashes_per_s": worst}, flash_events[:10], ["flash_per_s"]))
    return res
