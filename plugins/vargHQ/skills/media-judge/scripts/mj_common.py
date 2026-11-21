"""Shared helpers: probing, frame reading, facts, evidence images."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
THRESHOLDS = json.loads((HERE / "thresholds.json").read_text())
MODEL_DIR = Path(os.environ.get("MEDIA_JUDGE_MODELS", Path.home() / ".cache" / "media-judge"))


def th(name: str) -> float:
    return THRESHOLDS[name]["value"]


def th_meta(name: str) -> dict:
    t = THRESHOLDS[name]
    return {"name": name, "value": t["value"], "unit": t.get("unit", ""), "status": t["status"], "source": t.get("source", "")}


def run(cmd: list[str], check: bool = True, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=True, text=True, **kw)


def have(binary: str) -> bool:
    return shutil.which(binary) is not None


def fmt_t(t: float) -> str:
    m = int(t // 60)
    return f"{m:02d}:{t - m * 60:05.2f}"


def fetch_model(name: str, url: str) -> Path | None:
    """Download a small model file once. Returns None when offline."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    p = MODEL_DIR / name
    if p.exists() and p.stat().st_size > 0:
        return p
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "media-judge"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        p.write_bytes(data)
        return p
    except Exception:
        return None


@dataclass
class Probe:
    path: str
    width: int = 0
    height: int = 0
    fps: float = 0.0
    duration: float = 0.0
    vcodec: str = ""
    pix_fmt: str = ""
    color_range: str = ""
    color_space: str = ""
    bit_rate: int = 0
    has_audio: bool = False
    acodec: str = ""
    sample_rate: int = 0
    channels: int = 0
    v_start: float = 0.0
    a_start: float = 0.0
    pts: list = field(default_factory=list)
    decode_errors: list = field(default_factory=list)
    faststart: bool | None = None

    def to_json(self) -> dict:
        d = dict(self.__dict__)
        d.pop("pts")
        d["n_frames"] = len(self.pts)
        d["aspect"] = round(self.width / self.height, 4) if self.height else None
        deltas = np.diff(self.pts) if len(self.pts) > 1 else np.array([0.0])
        d["frame_interval_ms"] = {
            "median": round(float(np.median(deltas)) * 1000, 2),
            "max": round(float(np.max(deltas)) * 1000, 2),
        }
        d["vfr"] = bool(len(self.pts) > 1 and (np.max(deltas) > 1.5 * np.median(deltas)))
        return d


def probe(path: str, check_decode: bool = True) -> Probe:
    out = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path]).stdout
    info = json.loads(out)
    p = Probe(path=path)
    fmt = info.get("format", {})
    p.duration = float(fmt.get("duration", 0) or 0)
    p.bit_rate = int(fmt.get("bit_rate", 0) or 0)
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and not p.width:
            if s.get("disposition", {}).get("attached_pic"):
                continue
            p.width, p.height = int(s["width"]), int(s["height"])
            num, den = (s.get("avg_frame_rate") or "0/1").split("/")
            p.fps = float(num) / float(den) if float(den) else 0.0
            if not p.fps:
                num, den = (s.get("r_frame_rate") or "0/1").split("/")
                p.fps = float(num) / float(den) if float(den) else 0.0
            p.vcodec = s.get("codec_name", "")
            p.pix_fmt = s.get("pix_fmt", "")
            p.color_range = s.get("color_range", "")
            p.color_space = s.get("color_space", "")
            p.v_start = float(s.get("start_time", 0) or 0)
        elif s.get("codec_type") == "audio" and not p.has_audio:
            p.has_audio = True
            p.acodec = s.get("codec_name", "")
            p.sample_rate = int(s.get("sample_rate", 0) or 0)
            p.channels = int(s.get("channels", 0) or 0)
            p.a_start = float(s.get("start_time", 0) or 0)
    if p.width:
        pts_out = run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time", "-of", "csv=p=0", path]
        ).stdout
        pts = []
        for line in pts_out.splitlines():
            line = line.strip().rstrip(",")
            try:
                pts.append(float(line))
            except ValueError:
                pass
        p.pts = sorted(pts)
        if check_decode:
            err = run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-map", "0:v:0", "-f", "null", "-"], check=False).stderr
            p.decode_errors = [l.strip() for l in err.splitlines() if l.strip()][:20]
    return p


def read_frames(path: str, width: int, height: int | None = None):
    """Yield BGR frames resized to `width` wide, one per coded frame, with no frame rate conversion."""
    meta = probe(path, check_decode=False)
    if height is None:
        height = int(round(meta.height * width / meta.width / 2) * 2)
    cmd = [
        "ffmpeg", "-v", "error", "-nostdin", "-i", path, "-map", "0:v:0", "-fps_mode", "passthrough",
        "-vf", f"scale={width}:{height}:flags=area,format=bgr24", "-f", "rawvideo", "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    size = width * height * 3
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            yield np.frombuffer(buf, np.uint8).reshape(height, width, 3)
    finally:
        proc.stdout.close()
        proc.terminate()
        proc.wait()


def grab(path: str, t: float, width: int | None = None) -> np.ndarray | None:
    """One accurate frame at time t, at source size unless width is given."""
    vf = ["-vf", f"scale={width}:-2"] if width else []
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-ss", f"{max(t, 0):.3f}", "-i", path, "-frames:v", "1", *vf,
           "-f", "image2pipe", "-vcodec", "png", "-"]
    proc = subprocess.run(cmd, capture_output=True)
    if not proc.stdout:
        return None
    return cv2.imdecode(np.frombuffer(proc.stdout, np.uint8), cv2.IMREAD_COLOR)


def label_frame(img: np.ndarray, text: str) -> np.ndarray:
    out = img.copy()
    h = out.shape[0]
    scale = max(0.4, h / 700)
    (tw, th_), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    cv2.rectangle(out, (0, 0), (tw + 12, th_ + 12), (0, 0, 0), -1)
    cv2.putText(out, text, (6, th_ + 6), cv2.FONT_HERSHEY_SIMPLEX, scale, (255, 255, 255), 1, cv2.LINE_AA)
    return out


def strip(path: str, times: list[float], out: Path, width: int = 480, labels: list[str] | None = None) -> str | None:
    """Save a row of frames at the given times. This is how a finding shows its proof."""
    frames = []
    for i, t in enumerate(times):
        f = grab(path, t, width)
        if f is None:
            continue
        frames.append(label_frame(f, labels[i] if labels else fmt_t(t)))
    if not frames:
        return None
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), cv2.hconcat(frames), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return str(out)


def grid(images: list[np.ndarray], cols: int, out: Path) -> str | None:
    if not images:
        return None
    h, w = images[0].shape[:2]
    rows = []
    for i in range(0, len(images), cols):
        row = [cv2.resize(im, (w, h)) for im in images[i:i + cols]]
        while len(row) < cols:
            row.append(np.zeros((h, w, 3), np.uint8))
        rows.append(cv2.hconcat(row))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), cv2.vconcat(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return str(out)


def check(name: str, covers: str, state: str, measured: dict, events: list | None = None,
          thresholds: list | None = None, note: str = "") -> dict:
    """One fact record. state is clear, flagged, info or not_run. It is never a grade."""
    assert state in {"clear", "flagged", "info", "not_run"}
    return {"check": name, "covers": covers, "state": state, "measured": measured, "events": events or [],
            "thresholds": [th_meta(t) for t in (thresholds or [])], "note": note}


def not_run(name: str, covers: str, why: str) -> dict:
    return check(name, covers, "not_run", {}, note=why)


def lab_mean(bgr: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
    return lab.reshape(-1, 3).mean(axis=0)


def ciede2000(a: np.ndarray, b: np.ndarray) -> float:
    """CIEDE2000 between two Lab colours (L 0-100)."""
    L1, a1, b1 = a
    L2, a2, b2 = b
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1 = np.degrees(np.arctan2(b1, a1p)) % 360
    h2 = np.degrees(np.arctan2(b2, a2p)) % 360
    dL = L2 - L1
    dC = C2p - C1p
    if C1p * C2p == 0:
        dh = 0.0
    else:
        dh = h2 - h1
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
    dH = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh) / 2)
    Lm = (L1 + L2) / 2
    Cpm = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hm = h1 + h2
    elif abs(h1 - h2) <= 180:
        hm = (h1 + h2) / 2
    else:
        hm = (h1 + h2 + 360) / 2 if h1 + h2 < 360 else (h1 + h2 - 360) / 2
    T = (1 - 0.17 * np.cos(np.radians(hm - 30)) + 0.24 * np.cos(np.radians(2 * hm))
         + 0.32 * np.cos(np.radians(3 * hm + 6)) - 0.20 * np.cos(np.radians(4 * hm - 63)))
    dT = 30 * np.exp(-(((hm - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cpm ** 7 / (Cpm ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lm - 50) ** 2 / np.sqrt(20 + (Lm - 50) ** 2)
    Sc = 1 + 0.045 * Cpm
    Sh = 1 + 0.015 * Cpm * T
    Rt = -np.sin(np.radians(2 * dT)) * Rc
    return float(np.sqrt((dL / Sl) ** 2 + (dC / Sc) ** 2 + (dH / Sh) ** 2 + Rt * (dC / Sc) * (dH / Sh)))
