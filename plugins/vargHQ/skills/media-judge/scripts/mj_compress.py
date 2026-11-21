"""Item 7: dark scenes that break into bands and blocks after upload.
Encodes a copy the way a platform would, then measures banding (CAMBI) and blocking on both."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import cv2
import numpy as np

from mj_common import check, grab, label_frame, not_run, run, strip, th

PROFILES = {
    # Stand-ins for the platform encoder, not its settings. X's table lists 1280x720 at 2048K; the others are guesses
    # under their upload specs, because delivered ladders are not published. One real private upload beats all of them.
    "x": {"long_side": 1280, "kbps": 2048},
    "youtube": {"long_side": 1920, "kbps": 4000},
    "reels": {"long_side": 1920, "kbps": 3500},
    "tiktok": {"long_side": 1920, "kbps": 2500},
}


def _scale(w: int, h: int, long_side: int) -> tuple[int, int]:
    k = min(1.0, long_side / max(w, h))
    return int(round(w * k / 2)) * 2, int(round(h * k / 2)) * 2


def _has_libvmaf() -> bool:
    return "libvmaf" in run(["ffmpeg", "-hide_banner", "-filters"]).stdout


def cambi_series(main: str, ref: str, w: int, h: int, subsample: int) -> dict[int, dict]:
    with tempfile.TemporaryDirectory() as td:
        log = str(Path(td) / "vmaf.json")
        graph = (f"[0:v]scale={w}:{h}:flags=bicubic,format=yuv420p[a];[1:v]scale={w}:{h}:flags=bicubic,format=yuv420p[b];"
                 f"[a][b]libvmaf=feature=name=cambi:log_fmt=json:log_path={log}:n_subsample={subsample}:n_threads=4")
        run(["ffmpeg", "-v", "error", "-nostdin", "-i", main, "-i", ref, "-lavfi", graph, "-f", "null", "-"], check=False)
        try:
            data = json.loads(Path(log).read_text())
        except Exception:
            return {}
    out = {}
    for fr in data.get("frames", []):
        m = fr.get("metrics", {})
        out[int(fr["frameNum"])] = {"cambi": m.get("cambi"), "vmaf": m.get("vmaf")}
    return out


def block_series(path: str, w: int, h: int) -> list[float]:
    proc = run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vf",
                f"scale={w}:{h},format=gray,blockdetect,metadata=print:file=-", "-f", "null", "-"], check=False)
    return [float(v) for v in re.findall(r"lavfi\.block=([\d.]+)", proc.stdout)]


def compression_check(path: str, probe, shots: list[dict], luma: np.ndarray, t: np.ndarray, ev: Path, platform: str) -> list[dict]:
    covers = "7 dark scenes break into bands and blocks after upload"
    if not _has_libvmaf():
        return [not_run("upload_banding", covers, "This ffmpeg has no libvmaf filter, so CAMBI cannot run.")]
    prof = PROFILES.get(platform, PROFILES["x"])
    w, h = _scale(probe.width, probe.height, prof["long_side"])
    subsample = max(1, int(round(probe.fps / 8))) if probe.fps else 3
    res = []
    with tempfile.TemporaryDirectory() as td:
        sim = str(Path(td) / "upload.mp4")
        k = prof["kbps"]
        run(["ffmpeg", "-y", "-v", "error", "-nostdin", "-i", path, "-map", "0:v:0", "-vf", f"scale={w}:{h}:flags=bicubic,format=yuv420p",
             "-threads", "4", "-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{k}k", "-maxrate", f"{int(k * 1.5)}k", "-bufsize", f"{k * 2}k", sim])
        src_c = cambi_series(path, path, w, h, subsample)
        sim_c = cambi_series(sim, path, w, h, subsample)
        src_b = block_series(path, w, h)
        sim_b = block_series(sim, w, h)

        per_shot, events = [], []
        dark_limit = th("dark_luma")
        for s in shots:
            a, b = s["first_frame"], s["last_frame"]
            if b <= a:
                continue
            keys = [i for i in sim_c if a <= i <= b]
            if not keys:
                continue
            shot_luma = float(np.median(luma[a:b + 1]))
            before = [src_c[i]["cambi"] for i in keys if i in src_c and src_c[i]["cambi"] is not None]
            after = [sim_c[i]["cambi"] for i in keys if sim_c[i]["cambi"] is not None]
            vm = [sim_c[i]["vmaf"] for i in keys if sim_c[i]["vmaf"] is not None]
            if not after:
                continue
            blk_after = sim_b[a:b + 1]
            blk_before = src_b[a:b + 1]
            row = {"shot": s["index"], "t": s["start"], "t_end": s["end"], "median_luma": round(shot_luma, 1),
                   "dark": shot_luma < dark_limit,
                   "cambi_source": round(float(np.mean(before)), 2) if before else None,
                   "cambi_upload": round(float(np.mean(after)), 2),
                   "cambi_upload_max": round(float(np.max(after)), 2),
                   "block_source": round(float(np.mean(blk_before)), 2) if blk_before else None,
                   "block_upload": round(float(np.mean(blk_after)), 2) if blk_after else None,
                   "vmaf_upload": round(float(np.mean(vm)), 1) if vm else None}
            per_shot.append(row)
            if row["cambi_upload"] >= th("cambi_visible") and (row["dark"] or row["cambi_upload"] >= th("cambi_visible") * 1.5):
                worst = max(keys, key=lambda i: sim_c[i]["cambi"] or 0)
                tw = float(t[worst])
                row_e = dict(row)
                row_e["evidence"] = _evidence(path, sim, tw, ev / f"banding_{s['index']}.jpg", row)
                events.append(row_e)
    dark = [r for r in per_shot if r["dark"]]
    res.append(check("upload_banding", covers, "flagged" if events else "clear",
                     {"profile": platform, "simulated_size": f"{w}x{h}", "simulated_kbps": prof["kbps"],
                      "dark_shots": len(dark), "per_shot": per_shot,
                      "worst_dark_cambi_upload": max((r["cambi_upload_max"] for r in dark), default=None),
                      "worst_cambi_source": max((r["cambi_source"] or 0 for r in per_shot), default=None)},
                     events[:10], ["cambi_visible", "dark_luma"],
                     note="Simulated encode. The real encoder differs, so test the real upload when it matters."))
    return res


def _evidence(src: str, sim: str, t: float, out: Path, row: dict) -> str | None:
    a, b = grab(src, t, 640), grab(sim, t, 640)
    if a is None or b is None:
        return None
    # The lift makes bands easy to see for a model and for a person looking at a thumbnail.
    def lift(x):
        return np.clip(((x / 255.0) ** 0.5) * 255, 0, 255).astype(np.uint8)
    b = cv2.resize(b, (a.shape[1], a.shape[0]))
    cells = [label_frame(a, f"source CAMBI {row['cambi_source']}"), label_frame(b, f"upload sim CAMBI {row['cambi_upload']}"),
             label_frame(lift(a), "source, shadows lifted"), label_frame(lift(b), "upload sim, shadows lifted")]
    top, bot = cv2.hconcat(cells[:2]), cv2.hconcat(cells[2:])
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), cv2.vconcat([top, bot]), [cv2.IMWRITE_JPEG_QUALITY, 90])
    return str(out)
