#!/usr/bin/env python3
"""A video, GIF or picture -> a Telegram custom emoji pack laid out as a mosaic -> one message of it.

Offline by default: `plan`, `make`, `check` and `message` need no token and no network (`make` and the
video checks need ffmpeg with ffprobe on PATH). Only `publish` talks to Telegram, and only with
TELEGRAM_LIVE=1 and a bot token in an environment variable (TELEGRAM_TEST_BOT_TOKEN, or the variable
named by --token-env). The token is never printed. The source file never leaves the machine except as
the finished 100x100 tiles uploaded to the bot the user chose.

  py -3 scripts/emoji_mosaic.py plan clip.mp4                          # grid options for its shape
  py -3 scripts/emoji_mosaic.py make clip.mp4 --grid 8x4 --start 1.2 --duration 2.9 --out mosaic/
  py -3 scripts/emoji_mosaic.py make clip.mp4 --corners 120,40,1800,880 --round 48 --out mosaic/
  py -3 scripts/emoji_mosaic.py make logo.png --grid 6x3 --fit contain --out mosaic/
  py -3 scripts/emoji_mosaic.py check mosaic/            # or the ZIP the website's generator saved
  py -3 scripts/emoji_mosaic.py message mosaic/ --ids ids.json
  TELEGRAM_LIVE=1 TELEGRAM_TEST_BOT_TOKEN=... py -3 scripts/emoji_mosaic.py publish mosaic/ --owner 123456789

`make` writes mosaic.json (schema tg-emoji-mosaic/v1, the same one the website's generator puts in its
ZIP), tiles/ (row by row, left to right), canvas.png and preview.html (Telegram's gaps between emoji, light
and dark). Rules and sources: references/emoji-mosaic.md. Idea and seam preview after tg-emoji-mosaic (MIT, KISA).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import http.client
import json
import math
import os
import re
import shutil
import ssl
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
import zipfile

SCHEMA = "tg-emoji-mosaic/v1"
TILE = 100                      # stickers page: emoji are exactly 100x100 px, static and video
MAX_SECONDS = 3.0               # stickers page: video duration must not exceed 3 seconds
MAX_FPS = 30                    # stickers page: frame rate up to 30 FPS
MAX_VIDEO_BYTES = 256 * 1024    # stickers page: video size should not exceed 256 KB
MAX_INITIAL = 50                # createNewStickerSet: 1-50 initial stickers
MAX_SET = 200                   # addStickerToSet: emoji sticker sets can have up to 200 stickers
DEFAULT_MAX_EMOJI = 100         # appConfig message_animated_emoji_max; 100 observed, not documented as a number
SAFE_COLUMNS = 8                # Heuristic: a row of 8 fits a narrow phone bubble without wrapping
WIDE_COLUMNS = 12               # Heuristic: up to 12 fits most phones; check the narrowest one
DEFAULT_SECONDS = 2.9
DEFAULT_FPS = 30
DEFAULT_FALLBACK = "⬜"         # shown where a custom emoji can't be displayed
DEFAULT_TITLE = "Mosaic image via @hlixli"
STILL_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".avif", ".heic", ".heif"}
TARGET_EMOJI = 40                # Heuristic: the default grid stays at or under 40 tiles, larger emoji read better
EXIT_UNKNOWN = 5                 # the request may have reached Telegram: run publish again, it resumes
BITRATES = ("400k", "250k", "160k", "100k")


class MosaicError(Exception):
    """A rule of Telegram or of this tool would be broken; the message says which."""


# ---------------------------------------------------------------- grid

def grid_options(width: int, height: int, *, max_emoji: int = DEFAULT_MAX_EMOJI, max_cols: int = WIDE_COLUMNS,
                 limit: int = 8) -> list[dict]:
    """Grids for a source of width x height: closest shape first, then more emoji.

    `crop` is the share of the picture a cover fit cuts away to match the grid's shape."""
    if width <= 0 or height <= 0:
        raise MosaicError("the source has no size")
    want = width / height
    found = []
    for cols in range(1, max_cols + 1):
        for rows in range(1, max_emoji // cols + 1):
            ratio = cols / rows
            crop = 1 - min(ratio, want) / max(ratio, want)
            found.append({"grid": f"{cols}x{rows}", "cols": cols, "rows": rows, "emoji": cols * rows,
                          "crop": round(crop, 3), "columns": column_fit(cols)})
    useful = [g for g in found if g["emoji"] >= 4] or found
    useful.sort(key=lambda g: (round(g["crop"], 2), -g["emoji"]))
    return useful[:limit]


def column_fit(cols: int) -> str:
    """How a row of `cols` custom emoji is likely to fit a chat bubble (Heuristic, check on a real phone)."""
    if cols <= SAFE_COLUMNS:
        return "safe"
    if cols <= WIDE_COLUMNS:
        return "check-narrow-phone"
    return "likely-wraps"


def auto_grid(width: int, height: int, max_emoji: int = DEFAULT_MAX_EMOJI) -> tuple[int, int]:
    """The default grid: a safe column count, the shape within 5% if possible, then the most emoji up to
    TARGET_EMOJI (fewer, larger tiles read better in a chat)."""
    options = grid_options(width, height, max_emoji=min(max_emoji, MAX_SET), max_cols=SAFE_COLUMNS, limit=10_000)
    close = [g for g in options if g["crop"] <= 0.05] or options
    modest = [g for g in close if g["emoji"] <= TARGET_EMOJI] or close
    best = max(modest, key=lambda g: (g["emoji"], -g["crop"]))
    return best["cols"], best["rows"]


def parse_grid(text: str, max_emoji: int = DEFAULT_MAX_EMOJI) -> tuple[int, int]:
    m = re.fullmatch(r"\s*(\d+)\s*[xX×]\s*(\d+)\s*", text or "")
    if not m:
        raise MosaicError(f"grid must look like 8x4, got {text!r}")
    cols, rows = int(m.group(1)), int(m.group(2))
    if cols < 1 or rows < 1:
        raise MosaicError("a grid needs at least one column and one row")
    if cols * rows > max_emoji:
        raise MosaicError(f"{cols}x{rows} is {cols * rows} emoji; one message holds at most {max_emoji}")
    if cols * rows > MAX_SET:
        raise MosaicError(f"an emoji set holds at most {MAX_SET} emoji")
    return cols, rows


# ---------------------------------------------------------------- crop and fit

def parse_box(crop: str | None, corners: str | None, width: int, height: int) -> tuple[int, int, int, int]:
    """The part of the source to use, as x, y, w, h in source pixels. Default: the whole frame.

    --crop X,Y,W,H gives the top-left corner and the size; --corners X1,Y1,X2,Y2 gives two opposite corners."""
    if crop and corners:
        raise MosaicError("give --crop or --corners, not both")
    if not crop and not corners:
        return 0, 0, width, height
    nums = [float(v) for v in re.split(r"[,\s]+", (crop or corners).strip()) if v]
    if len(nums) != 4:
        raise MosaicError("a crop needs four numbers")
    if corners:
        x1, y1, x2, y2 = nums
        left, top, right, bottom = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
    else:
        left, top, right, bottom = nums[0], nums[1], nums[0] + nums[2], nums[1] + nums[3]
    x, y = int(round(left)), int(round(top))
    w, h = int(round(right)) - x, int(round(bottom)) - y
    if w < 8 or h < 8:
        raise MosaicError("the crop is too small")
    if x < 0 or y < 0 or x + w > width or y + h > height:
        raise MosaicError(f"the crop {x},{y},{w},{h} leaves the {width}x{height} frame")
    return x, y, w, h


def fit_filter(box: tuple[int, int, int, int], cols: int, rows: int, fit: str, background: str) -> str:
    """ffmpeg filters: source -> the chosen box -> a canvas of cols*100 x rows*100."""
    x, y, w, h = box
    cw, ch = cols * TILE, rows * TILE
    parts = ["format=rgba", f"crop={w}:{h}:{x}:{y}:exact=1"]
    if fit == "cover":      # fill the canvas, cut the overflow evenly from both sides
        parts += [f"scale={cw}:{ch}:force_original_aspect_ratio=increase:flags=lanczos", f"crop={cw}:{ch}"]
    elif fit == "contain":  # the whole box, padded to the canvas
        pad = "0x00000000" if background == "transparent" else f"0x{background.lstrip('#')}"
        parts += [f"scale={cw}:{ch}:force_original_aspect_ratio=decrease:flags=lanczos", "format=rgba",
                  f"pad={cw}:{ch}:(ow-iw)/2:(oh-ih)/2:color={pad}"]
    elif fit == "fill":     # stretch
        parts += [f"scale={cw}:{ch}:flags=lanczos"]
    else:
        raise MosaicError(f"unknown fit {fit!r}")
    return ",".join(parts)


def round_filter(radius: int, cols: int, rows: int) -> str:
    """Round the mosaic's four outer corners with an antialiased edge; keeps the source's own alpha."""
    cw, ch, r = cols * TILE, rows * TILE, radius
    dx = f"max(max({r}-(X+0.5)\\,(X+0.5)-{cw - r})\\,0)"
    dy = f"max(max({r}-(Y+0.5)\\,(Y+0.5)-{ch - r})\\,0)"
    cover = f"clip({r}+0.5-hypot({dx}\\,{dy})\\,0\\,1)"
    return f"format=rgba,geq=r='r(X\\,Y)':g='g(X\\,Y)':b='b(X\\,Y)':a='alpha(X\\,Y)*{cover}'"


def max_radius(cols: int, rows: int) -> int:
    return min(cols, rows) * TILE // 2


# ---------------------------------------------------------------- media probing

def _need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise MosaicError(f"{tool} is not on PATH; install ffmpeg (it brings ffprobe)")
    return path


def probe(path: str) -> dict:
    out = subprocess.run([_need("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        raise MosaicError(f"ffprobe can't read {os.path.basename(path)}: {out.stderr.strip()[:200]}")
    return json.loads(out.stdout or "{}")


def _rate(text: str | None) -> float:
    if not text or text in ("0/0",):
        return 0.0
    if "/" in text:
        a, b = text.split("/", 1)
        return float(a) / float(b) if float(b) else 0.0
    return float(text)


def source_info(path: str) -> dict:
    info = probe(path)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise MosaicError("the file has no picture or video stream")
    tags = {k.lower(): v for k, v in (video.get("tags") or {}).items()}
    ext = os.path.splitext(path)[1].lower()
    duration = float(video.get("duration") or info.get("format", {}).get("duration") or 0)
    frames = int(video.get("nb_frames") or 0)
    still = ext in STILL_EXT and (frames <= 1)
    pix = video.get("pix_fmt") or ""
    codec = video.get("codec_name") or ""
    vpx_alpha = tags.get("alpha_mode") == "1"
    decoder = (["-c:v", "libvpx-vp9" if codec == "vp9" else "libvpx"] if vpx_alpha and codec in ("vp8", "vp9") else [])
    maybe = vpx_alpha or bool(re.search(r"rgba|bgra|argb|abgr|yuva|gbrap|^ya|pal8", pix))
    return {"width": int(video["width"]), "height": int(video["height"]), "duration": 0.0 if still else duration,
            "fps": _rate(video.get("avg_frame_rate")) or _rate(video.get("r_frame_rate")), "still": still,
            "codec": codec, "alpha": maybe and _real_alpha(path, decoder), "decoder": decoder}


def _real_alpha(path: str, decoder: list[str]) -> bool:
    """True when the first frames really have see-through pixels (a GIF palette or an RGBA PNG often doesn't)."""
    proc = subprocess.run([_need("ffmpeg"), "-hide_banner", "-loglevel", "error", *decoder, "-i", path,
                           "-frames:v", "12", "-vf", "format=rgba,alphaextract,signalstats,"
                           "metadata=print:key=lavfi.signalstats.YMIN:file=-", "-f", "null", "-"],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    lows = [int(v) for v in re.findall(r"lavfi\.signalstats\.YMIN=(\d+)", proc.stdout)]
    return proc.returncode != 0 or not lows or min(lows) < 250


# ---------------------------------------------------------------- make

def _run_ffmpeg(args: list[str]) -> None:
    proc = subprocess.run([_need("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise MosaicError("ffmpeg failed: " + (proc.stderr.strip()[-600:] or "no message"))


TILE_FILE = re.compile(r"r\d{2}c\d{2}\.(webm|png)")


def tile_names(cols: int, rows: int, ext: str) -> list[str]:
    return [f"tiles/r{r + 1:02d}c{c + 1:02d}.{ext}" for r in range(rows) for c in range(cols)]


def _vp9_args(bitrate: str, alpha: bool, fps: int) -> list[str]:
    args = ["-an", "-c:v", "libvpx-vp9", "-b:v", bitrate, "-crf", "30", "-r", str(fps), "-deadline", "good",
            "-cpu-used", "2", "-row-mt", "1", "-pix_fmt", "yuva420p" if alpha else "yuv420p"]
    if alpha:
        args += ["-auto-alt-ref", "0"]
    return args + ["-f", "webm"]


def make(src: str, out: str, *, grid: str | None = None, crop: str | None = None, corners: str | None = None,
         fit: str = "cover", background: str = "transparent", radius: int = 0, start: float = 0.0,
         duration: float | None = None, fps: int = DEFAULT_FPS, pingpong: bool = False,
         fallback: str = DEFAULT_FALLBACK, max_emoji: int = DEFAULT_MAX_EMOJI, still: bool | None = None) -> dict:
    info = source_info(src)
    is_still = info["still"] if still is None else still
    cols, rows = parse_grid(grid, max_emoji) if grid else auto_grid(*_box_size(crop, corners, info), max_emoji)
    box = parse_box(crop, corners, info["width"], info["height"])
    if radius < 0 or radius > max_radius(cols, rows):
        raise MosaicError(f"--round must be 0..{max_radius(cols, rows)} px for a {cols}x{rows} grid")
    if not re.fullmatch(r"transparent|#?[0-9a-fA-F]{6}", background):
        raise MosaicError("--background is 'transparent' or a hex colour like #FFFFFF")
    fps = int(fps)
    if not 1 <= fps <= MAX_FPS:
        raise MosaicError(f"--fps must be 1..{MAX_FPS}")
    if info["fps"] >= 1:     # a 10 FPS GIF stays at 10: more frames would only spend the 256 KB budget
        fps = min(fps, max(1, round(info["fps"])))
    length = 0.0
    if not is_still:
        left = max(info["duration"] - start, 0.0) if info["duration"] else MAX_SECONDS
        length = min(duration if duration is not None else DEFAULT_SECONDS, left or MAX_SECONDS)
        if pingpong:
            length = min(length, MAX_SECONDS / 2 - 0.05)
        if length <= 0:
            raise MosaicError("nothing left to cut: --start is past the end of the video")
        if (length * 2 if pingpong else length) > MAX_SECONDS:
            raise MosaicError(f"a video emoji lasts at most {MAX_SECONDS:g} s")
    alpha = radius > 0 or info["alpha"] or (fit == "contain" and background == "transparent")

    os.makedirs(os.path.join(out, "tiles"), exist_ok=True)
    for name in os.listdir(os.path.join(out, "tiles")):   # only this tool's own tiles from an earlier run
        if TILE_FILE.fullmatch(name):
            os.remove(os.path.join(out, "tiles", name))
    chain = [fit_filter(box, cols, rows, fit, background)]
    if radius:
        chain.append(round_filter(radius, cols, rows))
    chain.append("format=rgba")
    decoder = info["decoder"]

    total = 0
    with tempfile.TemporaryDirectory(prefix="mosaic_") as tmp:
        canvas = os.path.join(tmp, "canvas.mkv")
        if is_still:
            seek = ["-ss", f"{start:.3f}"] if start and not info["still"] else []
            _run_ffmpeg([*seek, *decoder, "-i", src, "-vf", ",".join(chain), "-frames:v", "1",
                         os.path.join(out, "canvas.png")])
            names = tile_names(cols, rows, "png")
            _split_tiles(os.path.join(out, "canvas.png"), out, names, cols, lambda: ["-frames:v", "1"])
        else:
            frames = max(2 if pingpong else 1, round(length * fps))
            vf = ",".join(chain + [f"fps={fps}"])
            if pingpong:     # forward, then back without repeating the turn frame or the loop frame
                vf += (f",split[a][b];[b]reverse,trim=start_frame=1:end_frame={frames - 1},setpts=PTS-STARTPTS[r];"
                       "[a][r]concat=n=2:v=1:a=0")
            seek = ["-ss", f"{start:.3f}"] if start else []
            _run_ffmpeg([*seek, "-t", f"{length:.3f}", *decoder, "-i", src, "-an", "-filter_complex", vf,
                         "-c:v", "png", "-pix_fmt", "rgba", canvas])
            _run_ffmpeg(["-i", canvas, "-frames:v", "1", os.path.join(out, "canvas.png")])
            names = tile_names(cols, rows, "webm")
            total = frames + (max(frames - 2, 0) if pingpong else 0)
            _split_tiles(canvas, out, names, cols, lambda: ["-frames:v", str(total), *_vp9_args(BITRATES[0], alpha, fps)])
            for name in names:   # a tile over the size budget is encoded again, lower, on its own
                path = os.path.join(out, *name.split("/"))
                for bitrate in BITRATES[1:]:
                    if os.path.getsize(path) <= MAX_VIDEO_BYTES:
                        break
                    index = names.index(name)
                    r, c = divmod(index, cols)
                    _run_ffmpeg(["-i", canvas, "-vf", f"crop={TILE}:{TILE}:{c * TILE}:{r * TILE}", "-frames:v",
                                 str(total), *_vp9_args(bitrate, alpha, fps), path])
    manifest = {
        "schema": SCHEMA, "format": "static" if is_still else "video",
        "grid": {"cols": cols, "rows": rows}, "tile": TILE, "fallback": fallback, "tiles": names,
        "source": {"name": os.path.basename(src), "width": info["width"], "height": info["height"],
                   "box": dict(zip("xywh", box)), "fit": fit, "background": background,
                   "start": round(start, 3), "duration": 0 if is_still else round(total / fps, 3),
                   "fps": 0 if is_still else fps, "pingpong": pingpong},
        "round": radius, "alpha": alpha, "made_by": "telegram-bot-ui emoji_mosaic.py",
    }
    with open(os.path.join(out, "mosaic.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    write_preview(out, manifest)
    return manifest


def _box_size(crop, corners, info) -> tuple[int, int]:
    _, _, w, h = parse_box(crop, corners, info["width"], info["height"])
    return w, h


def _split_tiles(canvas: str, out: str, names: list[str], cols: int, codec_args) -> None:
    """Cut the canvas into tiles, 25 outputs per ffmpeg run (short command lines on Windows)."""
    for first in range(0, len(names), 25):
        batch = names[first:first + 25]
        labels = "".join(f"[s{i}]" for i in range(len(batch)))
        graph = [f"[0:v]split={len(batch)}{labels}" if len(batch) > 1 else "[0:v]null[s0]"]
        args = ["-i", canvas]
        for i, name in enumerate(batch):
            r, c = divmod(first + i, cols)
            graph.append(f"[s{i}]crop={TILE}:{TILE}:{c * TILE}:{r * TILE}[t{i}]")
        args += ["-filter_complex", ";".join(graph)]
        for i, name in enumerate(batch):
            args += ["-map", f"[t{i}]", *codec_args(), os.path.join(out, *name.split("/"))]
        _run_ffmpeg(args)


# ---------------------------------------------------------------- preview

def write_preview(out: str, manifest: dict) -> str:
    """preview.html at 2x: edge to edge (newer clients) on a light and a dark bubble, and with the gaps older
    clients leave (about 1 px between emoji and 5 px between rows at 22 px)."""
    cols = manifest["grid"]["cols"]
    tag = ("<video src='{0}' autoplay loop muted playsinline></video>" if manifest["format"] == "video"
           else "<img src='{0}' alt=''>")
    cells = "".join(tag.format(html.escape(n)) for n in manifest["tiles"])
    page = f"""<!doctype html><meta charset="utf-8"><title>Emoji mosaic preview</title>
<style>body{{font:14px system-ui,sans-serif;margin:24px;color:#0f172a}}.row{{display:flex;gap:24px;flex-wrap:wrap}}
.b{{padding:16px;border-radius:16px}}.l{{background:#fff;box-shadow:0 0 0 1px #cad5e2}}.d{{background:#212d3b}}
.g{{display:grid;grid-template-columns:repeat({cols},44px);gap:0}}.o .g{{column-gap:2px;row-gap:10px}}
.g>*{{width:44px;height:44px;display:block}}p{{color:#62748e;max-width:60ch}}h2{{font-size:13px;color:#62748e}}</style>
<h1>{cols}&times;{manifest['grid']['rows']} mosaic, {len(manifest['tiles'])} emoji</h1>
<p>Shown at 2x. Newer Telegram clients draw a row of custom emoji edge to edge; older ones leave about 1 px between
emoji and 5 px between rows, which splits text or thin lines on a seam. A preview, not proof: open the sent message on
the phones you target.</p>
<div class="row"><div><h2>Edge to edge, light</h2><div class="b l"><div class="g">{cells}</div></div></div>
<div><h2>Edge to edge, dark</h2><div class="b d"><div class="g">{cells}</div></div></div>
<div class="o"><h2>Older clients</h2><div class="b l"><div class="g">{cells}</div></div></div></div>
"""
    path = os.path.join(out, "preview.html")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(page)
    return path


# ---------------------------------------------------------------- reading a mosaic (folder or ZIP)

class Mosaic:
    """A made mosaic: its manifest and the bytes of each tile, from a folder or the website's ZIP."""

    def __init__(self, manifest: dict, blobs: dict[str, bytes]):
        self.manifest = manifest
        self.blobs = blobs

    @property
    def cols(self) -> int:
        return int(self.manifest["grid"]["cols"])

    @property
    def rows(self) -> int:
        return int(self.manifest["grid"]["rows"])

    @property
    def tiles(self) -> list[str]:
        return list(self.manifest["tiles"])

    def fingerprint(self) -> str:
        h = hashlib.sha256(f"{self.cols}x{self.rows}".encode())
        for name in self.tiles:
            h.update(hashlib.sha256(self.blobs[name]).digest())
        return h.hexdigest()


SAFE_NAME = re.compile(r"tiles/[A-Za-z0-9_.-]+\.(webm|png|webp)")
MANIFEST_MAX = 256 * 1024


def load_mosaic(path: str) -> Mosaic:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            names = set(zf.namelist())
            root = ""
            if "mosaic.json" not in names:   # a ZIP with one top folder
                tops = {n.split("/", 1)[0] for n in names if "/" in n}
                if len(tops) == 1 and f"{next(iter(tops))}/mosaic.json" in names:
                    root = next(iter(tops)) + "/"
            if root + "mosaic.json" not in names:
                raise MosaicError("the ZIP has no mosaic.json")
            if zf.getinfo(root + "mosaic.json").file_size > MANIFEST_MAX:
                raise MosaicError("mosaic.json is too large")
            manifest = json.loads(zf.read(root + "mosaic.json").decode("utf-8-sig"))
            _check_manifest(manifest)
            blobs = {}
            for name in manifest["tiles"]:
                if root + name not in names:
                    raise MosaicError(f"the ZIP lacks {name}")
                info = zf.getinfo(root + name)
                if info.file_size > MAX_VIDEO_BYTES * 4:
                    raise MosaicError(f"{name} is far too large for an emoji")
                blobs[name] = zf.read(root + name)
            return Mosaic(manifest, blobs)
    if not os.path.isdir(path):
        raise MosaicError(f"{path} is neither a mosaic folder nor a ZIP")
    if os.path.getsize(os.path.join(path, "mosaic.json")) > MANIFEST_MAX:
        raise MosaicError("mosaic.json is too large")
    with open(os.path.join(path, "mosaic.json"), encoding="utf-8-sig") as fh:
        manifest = json.load(fh)
    _check_manifest(manifest)
    blobs = {}
    for name in manifest["tiles"]:
        with open(os.path.join(path, *name.split("/")), "rb") as fh:
            blobs[name] = fh.read()
    return Mosaic(manifest, blobs)


def looks_like_emoji(text) -> bool:
    """One short emoji: no letters, digits outside keycaps, spaces or markup."""
    if not isinstance(text, str) or not 0 < len(text) <= 16:
        return False
    if "\u20e3" in text:
        return bool(re.fullmatch(r"[#*0-9]\ufe0f?\u20e3", text))
    if re.search(r"[A-Za-z0-9\s<>&]", text):
        return False
    # one picture: every part of a ZWJ sequence has one base character; a flag is two regional indicators
    for part in text.split("\u200d"):
        bases = [ch for ch in part if not (ch == "\ufe0f" or "\U0001f3fb" <= ch <= "\U0001f3ff"
                                           or "\U000e0020" <= ch <= "\U000e007f")]
        flags = [ch for ch in bases if "\U0001f1e6" <= ch <= "\U0001f1ff"]
        if not (len(bases) == 1 or (len(bases) == 2 and len(flags) == 2)):
            return False
    return True


def _check_manifest(manifest: dict) -> None:
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise MosaicError(f"not a {SCHEMA} manifest")
    grid = manifest.get("grid")
    if not isinstance(grid, dict) or not all(isinstance(grid.get(k), int) and grid[k] >= 1 for k in ("cols", "rows")):
        raise MosaicError("grid must be {\"cols\": N, \"rows\": N} with whole numbers from 1")
    cols, rows = grid["cols"], grid["rows"]
    if cols * rows > MAX_SET:
        raise MosaicError(f"{cols}x{rows} is more than the {MAX_SET} emoji a set holds")
    tiles = manifest.get("tiles") or []
    if len(tiles) != cols * rows:
        raise MosaicError(f"{cols}x{rows} needs {cols * rows} tiles, the manifest lists {len(tiles)}")
    if len(set(tiles)) != len(tiles) or not all(SAFE_NAME.fullmatch(t) for t in tiles):
        raise MosaicError("tile names must be unique files under tiles/")
    if manifest.get("format") not in ("video", "static"):
        raise MosaicError("format is 'video' or 'static'")
    if "fallback" in manifest and not looks_like_emoji(manifest["fallback"]):
        raise MosaicError("fallback must be one emoji")
    emoji = manifest.get("emoji")
    if emoji is not None and (not isinstance(emoji, list) or len(emoji) != len(tiles)
                              or not all(looks_like_emoji(e) for e in emoji)):
        raise MosaicError("emoji must list one emoji per tile")


# ---------------------------------------------------------------- check

def image_size(data: bytes) -> tuple[str, int, int] | None:
    """(kind, width, height) of a PNG or WEBP from its header, standard library only."""
    if len(data) < 30:
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        w, h = struct.unpack(">II", data[16:24])
        return "png", w, h
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X":
            return "webp", 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return "webp", w & 0x3FFF, h & 0x3FFF
        if chunk == b"VP8L":
            b = data[21:25]
            return "webp", 1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
    return None


def check(mosaic: Mosaic, *, max_emoji: int = DEFAULT_MAX_EMOJI) -> list[dict]:
    """Every rule a tile or the grid breaks. Video tiles are probed with ffprobe."""
    problems: list[dict] = []
    m = mosaic.manifest
    if mosaic.cols * mosaic.rows > max_emoji:
        problems.append({"code": "TOO_MANY_EMOJI", "detail": f"{mosaic.cols * mosaic.rows} > {max_emoji} per message"})
    if mosaic.cols > WIDE_COLUMNS:
        problems.append({"code": "ROW_MAY_WRAP", "detail": f"{mosaic.cols} columns; rows may wrap on phones",
                         "severity": "warning"})
    fmt = m["format"]
    with tempfile.TemporaryDirectory(prefix="mosaic_check_") as tmp:
        for name in mosaic.tiles:
            data = mosaic.blobs[name]
            where = {"tile": name}
            if fmt == "static":
                size = image_size(data)
                if not size:
                    problems.append({**where, "code": "NOT_PNG_OR_WEBP"})
                elif size[1:] != (TILE, TILE):
                    problems.append({**where, "code": "NOT_100X100", "detail": f"{size[1]}x{size[2]}"})
                continue
            if len(data) > MAX_VIDEO_BYTES:
                problems.append({**where, "code": "VIDEO_TOO_BIG", "detail": f"{len(data)} bytes > {MAX_VIDEO_BYTES}"})
            path = os.path.join(tmp, "t.webm")
            with open(path, "wb") as fh:
                fh.write(data)
            info = probe(path)
            streams = info.get("streams", [])
            video = next((s for s in streams if s.get("codec_type") == "video"), {})
            if "webm" not in (info.get("format", {}).get("format_name") or ""):
                problems.append({**where, "code": "NOT_WEBM"})
            if video.get("codec_name") != "vp9":
                problems.append({**where, "code": "NOT_VP9", "detail": str(video.get("codec_name"))})
            if (video.get("width"), video.get("height")) != (TILE, TILE):
                problems.append({**where, "code": "NOT_100X100", "detail": f"{video.get('width')}x{video.get('height')}"})
            if any(s.get("codec_type") == "audio" for s in streams):
                problems.append({**where, "code": "HAS_AUDIO"})
            seconds = float(info.get("format", {}).get("duration") or video.get("duration") or 0)
            if seconds > MAX_SECONDS + 0.001:
                problems.append({**where, "code": "VIDEO_TOO_LONG", "detail": f"{seconds:.3f} s"})
            fps = _rate(video.get("avg_frame_rate")) or _rate(video.get("r_frame_rate"))
            if fps > MAX_FPS + 0.01:
                problems.append({**where, "code": "FPS_TOO_HIGH", "detail": f"{fps:g}"})
    return problems


# ---------------------------------------------------------------- message

def utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def mosaic_message(ids: list[str], cols: int, fallback: str | list[str] = DEFAULT_FALLBACK) -> dict:
    """sendMessage text and entities: one fallback emoji per tile, a line break after each row, one
    custom_emoji entity per emoji. Offsets and lengths are UTF-16 code units (Bot API MessageEntity)."""
    if not ids or len(set(ids)) != len(ids):
        raise MosaicError("ids must be a non-empty list without repeats")
    if not all(re.fullmatch(r"\d{1,20}", str(i)) for i in ids):
        raise MosaicError("a custom_emoji_id is a string of digits")
    text, entities = "", []
    for i, cid in enumerate(ids):
        alt = (fallback[i] if isinstance(fallback, list) else fallback) or DEFAULT_FALLBACK
        if i and i % cols == 0:
            text += "\n"
        entities.append({"type": "custom_emoji", "offset": utf16_len(text), "length": utf16_len(alt),
                         "custom_emoji_id": str(cid)})
        text += alt
    return {"text": text, "entities": entities}


def mosaic_html(ids: list[str], cols: int, fallback: str | list[str] = DEFAULT_FALLBACK) -> str:
    alts = fallback if isinstance(fallback, list) else [fallback] * len(ids)
    cells = [f'<tg-emoji emoji-id="{i}">{alts[n] or DEFAULT_FALLBACK}</tg-emoji>' for n, i in enumerate(ids)]
    return "\n".join("".join(cells[r:r + cols]) for r in range(0, len(cells), cols))


def tile_emoji(manifest: dict) -> list[str]:
    """The emoji behind each tile: the manifest's per-tile list (the website writes one), else its fallback."""
    fallback = manifest.get("fallback") or DEFAULT_FALLBACK
    per_tile = manifest.get("emoji") or []
    return [(per_tile[i] if i < len(per_tile) and per_tile[i] else fallback) for i in range(len(manifest["tiles"]))]


# ---------------------------------------------------------------- publish (live)

class OutcomeUnknown(Exception):
    """The request may have reached Telegram; read the set back before trying again."""


class TelegramError(Exception):
    def __init__(self, method: str, code: int, description: str):
        super().__init__(f"{method}: {code} {description}")
        self.code, self.description = code, description


class Bot:
    """Bot API over urllib: JSON bodies, multipart for uploads, waits out 429. Never prints the token."""

    def __init__(self, token: str, *, base_url: str = "https://api.telegram.org", timeout: float = 120.0,
                 sleep=time.sleep, log=lambda line: print(line, file=sys.stderr, flush=True)):
        self._prefix = f"{base_url}/bot{token}/"
        self._timeout, self._sleep, self._log = timeout, sleep, log

    def __repr__(self) -> str:
        return "Bot(<token hidden>)"

    def call(self, method: str, params: dict, files: dict[str, tuple[str, bytes, str]] | None = None):
        for attempt in range(8):
            if files:
                boundary = uuid.uuid4().hex
                body = _multipart(params, files, boundary)
                headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
            else:
                body = json.dumps(params, ensure_ascii=False).encode("utf-8")
                headers = {"Content-Type": "application/json"}
            req = urllib.request.Request(self._prefix + method, data=body, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as err:
                if err.code >= 500:          # the server may have done the work before failing
                    raise OutcomeUnknown(f"{method}: HTTP {err.code}") from None
                try:
                    payload = json.loads(err.read().decode("utf-8"))
                except (ValueError, http.client.HTTPException):
                    raise OutcomeUnknown(f"{method}: unreadable HTTP {err.code} answer") from None
            except (TimeoutError, ConnectionError, urllib.error.URLError, http.client.HTTPException, ssl.SSLError,
                    ValueError) as err:
                raise OutcomeUnknown(f"{method}: {type(err).__name__}") from None
            if payload.get("ok"):
                return payload.get("result")
            wait = (payload.get("parameters") or {}).get("retry_after")
            if payload.get("error_code") == 429 and wait:
                self._log(f"{method}: Telegram asks to wait {wait} s")
                self._sleep(float(wait) + 1)
                continue
            raise TelegramError(method, int(payload.get("error_code") or 0), str(payload.get("description")))
        raise TelegramError(method, 429, "still rate limited after 8 tries")


def _multipart(params: dict, files: dict[str, tuple[str, bytes, str]], boundary: str) -> bytes:
    out = bytearray()
    for key, value in params.items():
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{text}\r\n").encode("utf-8")
    for key, (filename, data, mime) in files.items():
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"; filename=\"{filename}\"\r\n"
                f"Content-Type: {mime}\r\n\r\n").encode("utf-8")
        out += data + b"\r\n"
    out += f"--{boundary}--\r\n".encode("utf-8")
    return bytes(out)


def set_name(fingerprint: str, bot_username: str) -> str:
    """createNewStickerSet name rules: letters, digits, underscores, begins with a letter, no double
    underscore, ends in _by_<bot_username>, 1-64 characters."""
    name = f"mosaic_{fingerprint[:10]}_by_{bot_username}".lower()
    if len(name) > 64 or "__" in name or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
        raise MosaicError(f"can't build a valid set name for @{bot_username}")
    return name


def _read_set(bot, name: str):
    try:
        return bot.call("getStickerSet", {"name": name})
    except TelegramError as err:
        if err.code == 400:
            return None
        raise


def preflight(mosaic: Mosaic, max_emoji: int = DEFAULT_MAX_EMOJI) -> list[dict]:
    """Every blocking problem: the full check when ffprobe is installed, else the header checks."""
    problems = check(mosaic, max_emoji=max_emoji) if shutil.which("ffprobe") else check_light(mosaic)
    if not shutil.which("ffprobe") and mosaic.cols * mosaic.rows > max_emoji:
        problems.append({"code": "TOO_MANY_EMOJI", "detail": f"{mosaic.cols * mosaic.rows} > {max_emoji} per message"})
    return [p for p in problems if p.get("severity") != "warning"]


def thumbnail_index(mosaic: Mosaic, choice: str) -> int | None:
    """Which tile becomes the set's icon: the centre by default (a corner tile can be transparent)."""
    if choice == "none":
        return None
    if choice == "first":
        return 0
    if choice == "center":
        return (mosaic.rows // 2) * mosaic.cols + mosaic.cols // 2
    index = int(choice)
    if not 0 <= index < len(mosaic.tiles):
        raise MosaicError(f"--thumbnail must be center, first, none or 0..{len(mosaic.tiles) - 1}")
    return index


def publish(bot, mosaic: Mosaic, *, owner: int, title: str = DEFAULT_TITLE, send_to: int | None = None,
            send: bool = True, thumbnail: str = "center", max_emoji: int = DEFAULT_MAX_EMOJI,
            log=lambda line: print(line, file=sys.stderr, flush=True)) -> dict:
    """Upload the tiles, create or finish the set, read it back, set its icon, send the mosaic, check what
    came back.

    Idempotent for the set: its name comes from the tiles' bytes, so a second run finishes the same set. Each
    run with send=True sends the message again; the CLI skips it when --save already holds a message_id."""
    problems = preflight(mosaic, max_emoji)
    if problems:
        raise MosaicError("fix the tiles first: " + json.dumps(problems[:3], ensure_ascii=False))
    thumb = thumbnail_index(mosaic, thumbnail)
    if not 1 <= len(title) <= 64:
        raise MosaicError("the set title is 1-64 characters")
    me = bot.call("getMe", {})
    name = set_name(mosaic.fingerprint(), me["username"])
    fmt = mosaic.manifest["format"]
    alts = tile_emoji(mosaic.manifest)
    tiles = mosaic.tiles
    current = _read_set(bot, name)
    have = len(current["stickers"]) if current else 0
    if current and current.get("sticker_type") != "custom_emoji":
        raise MosaicError(f"{name} exists and is not a custom emoji set")
    if have > len(tiles):
        raise MosaicError(f"{name} already holds {have} stickers, more than the {len(tiles)} tiles")

    def upload(name_: str) -> dict:
        alt = alts[tiles.index(name_)]
        data = mosaic.blobs[name_]
        mime = "video/webm" if fmt == "video" else ("image/png" if name_.endswith(".png") else "image/webp")
        sticker_format = "video" if fmt == "video" else "static"
        for attempt in range(3):
            try:
                f = bot.call("uploadStickerFile", {"user_id": owner, "sticker_format": sticker_format},
                             {"sticker": (os.path.basename(name_), data, mime)})
                break
            except OutcomeUnknown:      # an upload only returns a file; trying again is harmless
                if attempt == 2:
                    raise
        return {"sticker": f["file_id"], "format": sticker_format, "emoji_list": [alt]}

    if have == 0:
        first = tiles[:MAX_INITIAL]
        log(f"uploading {len(first)} of {len(tiles)} tiles, then creating {name}")
        stickers = [upload(t) for t in first]
        try:
            bot.call("createNewStickerSet", {"user_id": owner, "name": name, "title": title,
                                             "sticker_type": "custom_emoji", "stickers": stickers})
        except OutcomeUnknown:
            if not _read_set(bot, name):
                raise
        current = _read_set(bot, name)
        have = len(current["stickers"]) if current else 0
    for index in range(have, len(tiles)):
        log(f"adding tile {index + 1}/{len(tiles)}")
        sticker = upload(tiles[index])
        try:
            bot.call("addStickerToSet", {"user_id": owner, "name": name, "sticker": sticker})
        except OutcomeUnknown:
            again = _read_set(bot, name)
            if not again or len(again["stickers"]) <= index:
                raise
    final = _read_set(bot, name) or {}
    ids = [s.get("custom_emoji_id") for s in final.get("stickers", [])]
    if final.get("sticker_type") != "custom_emoji" or len(ids) != len(tiles) or len(set(ids)) != len(ids) \
            or not all(ids):
        raise MosaicError(f"the set {name} holds {len(ids)} emoji, expected {len(tiles)}; run publish again")
    if thumb is not None:
        try:
            bot.call("setCustomEmojiStickerSetThumbnail", {"name": name, "custom_emoji_id": ids[thumb]})
        except (TelegramError, OutcomeUnknown) as err:
            log(f"the set works, but its icon wasn't set: {err}")
    result = {"set": name, "link": f"https://t.me/addemoji/{name}", "grid": f"{mosaic.cols}x{mosaic.rows}",
              "ids": ids, "message_id": None, "custom_emoji_sent": None, "expected": len(ids), "delivered": None}
    if send:
        body = mosaic_message(ids, mosaic.cols, alts)
        sent = bot.call("sendMessage", {"chat_id": send_to or owner, **body})
        got = sum(1 for e in sent.get("entities", []) if e.get("type") == "custom_emoji")
        result.update(message_id=sent.get("message_id"), custom_emoji_sent=got, delivered=got == len(ids))
    return result


def plan_publish(mosaic: Mosaic, *, bot_username: str, existing: int = 0, thumbnail: str = "center",
                 send_to: int | None = None, owner: int | None = None) -> dict:
    """What publish would do, without doing it."""
    name = set_name(mosaic.fingerprint(), bot_username)
    tiles = len(mosaic.tiles)
    create = 0 if existing else min(MAX_INITIAL, tiles)
    thumb = thumbnail_index(mosaic, thumbnail)
    return {"set": name, "link": f"https://t.me/addemoji/{name}", "tiles": tiles, "already_in_set": existing,
            "uploads": tiles - existing, "create_with": create, "add_one_by_one": tiles - existing - create,
            "thumbnail_tile": None if thumb is None else mosaic.tiles[thumb], "send_to": send_to or owner}


def owners_from_updates(updates: list[dict]) -> list[dict]:
    """People who wrote to the bot, from a getUpdates answer: the numeric id publish needs for --owner."""
    seen: dict[int, dict] = {}
    for update in updates:
        for key in ("message", "edited_message", "callback_query", "my_chat_member"):
            who = (update.get(key) or {}).get("from")
            if who and not who.get("is_bot"):
                seen[who["id"]] = {"id": who["id"], "username": who.get("username"),
                                   "first_name": who.get("first_name"), "is_premium": bool(who.get("is_premium"))}
    return list(seen.values())


def check_light(mosaic: Mosaic) -> list[dict]:
    """The checks that need no ffprobe: sizes, counts, static headers."""
    problems = []
    if mosaic.cols * mosaic.rows > MAX_SET:
        problems.append({"code": "SET_TOO_BIG"})
    for name in mosaic.tiles:
        data = mosaic.blobs[name]
        if mosaic.manifest["format"] == "video":
            if len(data) > MAX_VIDEO_BYTES:
                problems.append({"tile": name, "code": "VIDEO_TOO_BIG"})
            if data[:4] != b"\x1a\x45\xdf\xa3":
                problems.append({"tile": name, "code": "NOT_WEBM"})
        else:
            size = image_size(data)
            if not size or size[1:] != (TILE, TILE):
                problems.append({"tile": name, "code": "NOT_100X100"})
    return problems


# ---------------------------------------------------------------- CLI

def _emit(obj, as_json: bool, text: str) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2) if as_json else text)


def _live_token(env_name: str) -> str | None:
    token = os.environ.get(env_name)
    return token if os.environ.get("TELEGRAM_LIVE") == "1" and token else None


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="emoji_mosaic.py", description=__doc__.split("\n\n")[0],
                                 epilog="Exit codes: 0 ok, 1 a rule or Telegram refused, 2 usage, 4 live mode not "
                                        f"enabled, {EXIT_UNKNOWN} outcome unknown (run publish again: it resumes).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="grid options for a source's shape")
    p.add_argument("src", nargs="?")
    p.add_argument("--size", help="WIDTHxHEIGHT instead of a file")
    p.add_argument("--crop"), p.add_argument("--corners")
    p.add_argument("--max-emoji", type=int, default=DEFAULT_MAX_EMOJI)
    p.add_argument("--json", action="store_true")

    m = sub.add_parser("make", help="tiles, canvas.png, preview.html and mosaic.json; offline")
    m.add_argument("src")
    m.add_argument("--out", default="mosaic")
    m.add_argument("--grid", help="COLSxROWS, e.g. 8x4; default: picked from the shape")
    m.add_argument("--crop", help="X,Y,W,H in source pixels: top-left corner and size")
    m.add_argument("--corners", help="X1,Y1,X2,Y2 in source pixels: two opposite corners")
    m.add_argument("--fit", choices=("cover", "contain", "fill"), default="cover")
    m.add_argument("--background", default="transparent", help="padding for --fit contain: transparent or #RRGGBB")
    m.add_argument("--round", type=int, default=0, help="round the mosaic's outer corners, radius in canvas px")
    m.add_argument("--start", type=float, default=0.0)
    m.add_argument("--duration", type=float, help=f"seconds, at most {MAX_SECONDS:g} (default {DEFAULT_SECONDS})")
    m.add_argument("--fps", type=int, default=DEFAULT_FPS)
    m.add_argument("--pingpong", action="store_true", help="play forward then back, for a seamless loop")
    m.add_argument("--still", action="store_true", help="use the first frame only: static PNG tiles")
    m.add_argument("--fallback", default=DEFAULT_FALLBACK)
    m.add_argument("--max-emoji", type=int, default=DEFAULT_MAX_EMOJI)
    m.add_argument("--json", action="store_true")

    c = sub.add_parser("check", help="every Telegram rule a mosaic folder or ZIP breaks")
    c.add_argument("path")
    c.add_argument("--max-emoji", type=int, default=DEFAULT_MAX_EMOJI)
    c.add_argument("--json", action="store_true")

    g = sub.add_parser("message", help="sendMessage text and entities from the set's ids; offline")
    g.add_argument("path")
    g.add_argument("--ids", required=True, help="JSON: a list of custom_emoji_id, or publish.json, or getStickerSet")
    g.add_argument("--html", action="store_true", help="<tg-emoji> HTML instead of entities")

    u = sub.add_parser("publish", help="live: create the pack with your bot and send the mosaic")
    u.add_argument("path")
    u.add_argument("--owner", type=int, required=True, help="numeric Telegram user id of the pack's owner")
    u.add_argument("--title", default=DEFAULT_TITLE)
    u.add_argument("--send-to", type=int, help="chat id for the mosaic message; default: the owner")
    u.add_argument("--token-env", default="TELEGRAM_TEST_BOT_TOKEN", help="name of the variable holding the token")
    u.add_argument("--save", help="write the result (set, link, ids, message_id) to this JSON file")
    u.add_argument("--thumbnail", default="center", help="the set's icon: center, first, none or a tile index")
    u.add_argument("--no-send", action="store_true", help="create the set only; don't send the mosaic")
    u.add_argument("--resend", action="store_true", help="send the mosaic again although --save holds a message_id")
    u.add_argument("--dry-run", action="store_true", help="check and show the plan; no writes to Telegram")
    u.add_argument("--bot-username", help="for --dry-run without live mode: the bot that will own the set name")
    u.add_argument("--max-emoji", type=int, default=DEFAULT_MAX_EMOJI)

    o = sub.add_parser("owner", help="live, read-only: numeric ids of people who wrote /start to the bot")
    o.add_argument("--token-env", default="TELEGRAM_TEST_BOT_TOKEN")

    d = sub.add_parser("delete", help="live: delete a set this bot created (an orphan or a mistake)")
    d.add_argument("name")
    d.add_argument("--yes", action="store_true", help="required: the set and its emoji are gone for everyone")
    d.add_argument("--token-env", default="TELEGRAM_TEST_BOT_TOKEN")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "plan":
            if a.size:
                w, h = (int(v) for v in a.size.lower().split("x"))
            elif a.src:
                info = source_info(a.src)
                w, h = _box_size(a.crop, a.corners, info)
            else:
                ap.error("plan needs a file or --size")
            options = grid_options(w, h, max_emoji=a.max_emoji)
            cols, rows = auto_grid(w, h, a.max_emoji)
            lines = [f"{w}x{h}: default {cols}x{rows}"] + [
                f"  {o['grid']:>6}  {o['emoji']:>3} emoji  crop {o['crop'] * 100:4.1f}%  {o['columns']}" for o in options]
            _emit({"size": [w, h], "default": f"{cols}x{rows}", "options": options}, a.json, "\n".join(lines))
            return 0
        if a.cmd == "make":
            manifest = make(a.src, a.out, grid=a.grid, crop=a.crop, corners=a.corners, fit=a.fit,
                            background=a.background, radius=a.round, start=a.start, duration=a.duration,
                            fps=a.fps, pingpong=a.pingpong, fallback=a.fallback, max_emoji=a.max_emoji,
                            still=True if a.still else None)
            problems = check(load_mosaic(a.out), max_emoji=a.max_emoji)
            g_ = manifest["grid"]
            text = (f"{g_['cols']}x{g_['rows']} = {len(manifest['tiles'])} {manifest['format']} tiles in {a.out}; "
                    f"look at {os.path.join(a.out, 'preview.html')} before publishing\n"
                    + ("\n".join(f"  {p['code']} {p.get('tile', '')} {p.get('detail', '')}" for p in problems)
                       or "  every tile meets Telegram's rules"))
            _emit({"manifest": manifest, "problems": problems}, a.json, text)
            return 1 if any(p.get("severity") != "warning" for p in problems) else 0
        if a.cmd == "check":
            problems = check(load_mosaic(a.path), max_emoji=a.max_emoji)
            errors = [p for p in problems if p.get("severity") != "warning"]
            _emit({"problems": problems, "ok": not errors}, a.json,
                  "\n".join(f"{p['code']} {p.get('tile', '')} {p.get('detail', '')}" for p in problems) or "ok")
            return 1 if errors else 0
        if a.cmd == "message":
            mosaic = load_mosaic(a.path)
            with open(a.ids, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                data = data.get("ids") or [s["custom_emoji_id"] for s in
                                           (data.get("result", data).get("stickers") or [])]
            fallback = tile_emoji(mosaic.manifest)
            if len(data) != len(mosaic.tiles):
                raise MosaicError(f"{len(data)} ids for {len(mosaic.tiles)} tiles")
            out = mosaic_html(data, mosaic.cols, fallback) if a.html else mosaic_message(data, mosaic.cols, fallback)
            print(out if a.html else json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        if a.cmd == "publish":
            mosaic = load_mosaic(a.path)
            token = _live_token(a.token_env)
            if a.dry_run:
                problems = preflight(mosaic, a.max_emoji)
                existing, username = 0, a.bot_username
                if token:
                    bot = Bot(token)
                    username = bot.call("getMe", {})["username"]
                    current = _read_set(bot, set_name(mosaic.fingerprint(), username))
                    existing = len(current["stickers"]) if current else 0
                if not username:
                    raise MosaicError("--dry-run needs live mode or --bot-username to name the set")
                plan = plan_publish(mosaic, bot_username=username, existing=existing, thumbnail=a.thumbnail,
                                    send_to=None if a.no_send else a.send_to, owner=None if a.no_send else a.owner)
                print(json.dumps({"plan": plan, "problems": problems}, ensure_ascii=False, indent=2))
                return 1 if problems else 0
            if not token:
                print(f"publish is live: set TELEGRAM_LIVE=1 and the bot token in {a.token_env}", file=sys.stderr)
                return 4
            previous = None
            if a.save and os.path.isfile(a.save):
                with open(a.save, encoding="utf-8-sig") as fh:
                    previous = json.load(fh)
            name_now = None
            send = not a.no_send
            if send and previous and previous.get("message_id") and not a.resend:
                bot = Bot(token)
                name_now = set_name(mosaic.fingerprint(), bot.call("getMe", {})["username"])
                if previous.get("set") == name_now:
                    send = False
                    print(f"the mosaic was already sent (message {previous['message_id']}); --resend sends it again",
                          file=sys.stderr)
            result = publish(Bot(token), mosaic, owner=a.owner, title=a.title, send_to=a.send_to, send=send,
                             thumbnail=a.thumbnail, max_emoji=a.max_emoji)
            if not send and previous and previous.get("set") == result["set"]:
                for key in ("message_id", "custom_emoji_sent", "delivered"):
                    result[key] = previous.get(key)
            if a.save:
                with open(a.save, "w", encoding="utf-8", newline="\n") as fh:
                    json.dump(result, fh, ensure_ascii=False, indent=2)
            print(json.dumps({k: v for k, v in result.items() if k != "ids"}, ensure_ascii=False, indent=2))
            if result["delivered"] is False:
                print("NOT DONE: the message came back without every custom emoji. The bot can't use custom emoji "
                      "in that chat: its owner (the bot's, not the pack's) has no Telegram Premium, or it is a "
                      "channel and the bot has no Fragment usernames.", file=sys.stderr)
                return 1
            return 0
        if a.cmd == "owner":
            token = _live_token(a.token_env)
            if not token:
                print(f"owner is live: set TELEGRAM_LIVE=1 and the bot token in {a.token_env}", file=sys.stderr)
                return 4
            try:
                updates = Bot(token).call("getUpdates", {"limit": 100, "timeout": 0})
            except TelegramError as err:
                if err.code == 409:
                    raise MosaicError("the bot has a webhook, so getUpdates is off; ask the person for their id "
                                      "(@userinfobot shows it)") from None
                raise
            people = owners_from_updates(updates or [])
            print(json.dumps(people, ensure_ascii=False, indent=2) if people else
                  "nobody has written to the bot yet: send it /start from the account that will own the pack")
            return 0 if people else 1
        if a.cmd == "delete":
            token = _live_token(a.token_env)
            if not token:
                print(f"delete is live: set TELEGRAM_LIVE=1 and the bot token in {a.token_env}", file=sys.stderr)
                return 4
            bot = Bot(token)
            username = bot.call("getMe", {})["username"].lower()
            if not a.name.lower().endswith(f"_by_{username}"):
                raise MosaicError(f"{a.name} wasn't created by @{username}; a bot can delete only its own sets")
            if not a.yes:
                print(f"this deletes {a.name} for everyone, with every emoji in it; add --yes", file=sys.stderr)
                return 2
            bot.call("deleteStickerSet", {"name": a.name})
            print(f"deleted {a.name}")
            return 0
    except OutcomeUnknown as err:
        print(f"outcome unknown: {err}. Run the same command again: publish reads the set back and resumes.",
              file=sys.stderr)
        return EXIT_UNKNOWN
    except (MosaicError, TelegramError, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile,
            struct.error) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
