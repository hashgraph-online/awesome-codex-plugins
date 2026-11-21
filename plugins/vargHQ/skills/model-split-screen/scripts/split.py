#!/usr/bin/env python3
"""Same prompt, two models: two clips side by side (16:9) or stacked (9:16), each with its name and its
real cost and time under it, started on the same frame. Labels are drawn with Pillow, so it works with
an ffmpeg built without drawtext. Needs Pillow (pip install pillow).

  python3 split.py --left fable.mp4 --left-name "Claude Fable 5.2" --left-stats "1 h 57 min · \\$81.10" \\
                   --right opus.mp4 --right-name "Claude Opus 5.5" --right-stats "3 h 11 min · \\$45.97" \\
                   --title "Same prompt, two models" --prompt "Cathedral of ice, a ship, a whale" -o split.mp4

  --layout stack     1080×1920 for Reels/TikTok/Shorts (left on top), default side: 1920×1080
  --blind 2.5        labels read "A" and "B" until the last 2.5 s, then the names and stats appear
  --winner left      an orange (#ff5315) frame around that panel (after the reveal when --blind)
  --duration 12      cut both to 12 s (default: the longer clip; the shorter one holds its last frame)
  --music bed.mp3    a music bed, faded out over the last second, -14 LUFS (default: no audio)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BG = "0x0b0b0d"
INK = "#f4f1ea"
DIM = "#a7a39b"
ACCENT_TEXT = "#ff5315"
ACCENT = "0xff5315"

FONTS = [
    os.path.expanduser("~/Library/Fonts/Inter-Bold.otf"),
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONTS_REG = [
    os.path.expanduser("~/Library/Fonts/Inter-SemiBold.otf"),
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def first(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    sys.exit("no font found: pass --font /path/to/Bold.ttf")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(cmd[:6])}…\n{r.stderr[-1500:]}")
    return r.stdout


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path])
    return float(json.loads(out)["format"]["duration"])


def text_png(path, w, h, lines, bold, reg):
    """A transparent PNG w×h with lines = [(text, size, color, bold?)] stacked and centered. Pillow draws the
    text (ImageMagick and ffmpeg builds often lack FreeType: no -annotate, no drawtext)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fonts = [ImageFont.truetype(bold if is_bold else reg, size) for _, size, _, is_bold in lines]
    heights = [int(size * 1.3) for _, size, _, _ in lines]
    y = (h - sum(heights)) // 2
    for (text, size, color, _), font, lh in zip(lines, fonts, heights):
        while d.textlength(text, font=font) > w - 40 and len(text) > 4:  # shorten what does not fit
            text = text[:-2].rstrip() + "…"
        d.text((w // 2, y + lh // 2), text, font=font, fill=color, anchor="mm")
        y += lh
    img.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--left", required=True)
    ap.add_argument("--right", required=True)
    ap.add_argument("--left-name", required=True)
    ap.add_argument("--right-name", required=True)
    ap.add_argument("--left-stats", default="")
    ap.add_argument("--right-stats", default="")
    ap.add_argument("--title", default="Same prompt, two models")
    ap.add_argument("--prompt", default="", help="one line under the title (shorten long prompts)")
    ap.add_argument("--layout", choices=["side", "stack"], default="side")
    ap.add_argument("--blind", type=float, default=0.0, help="reveal the names this many seconds before the end")
    ap.add_argument("--winner", choices=["left", "right"], default=None)
    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--music", default=None)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--font", default=None)
    ap.add_argument("-o", "--out", default="split.mp4")
    a = ap.parse_args()

    bold = a.font or first(FONTS)
    reg = first(FONTS_REG)
    dur = a.duration or max(duration(a.left), duration(a.right))
    tmp = Path(tempfile.mkdtemp(prefix="split-"))

    if a.layout == "side":
        W, H, pw, ph, gap = 1920, 1080, 928, 522, 24
        top = 250  # title 100–230, panels 250–772, labels 790–940: the block sits in the middle
        boxes = [((W - 2 * pw - gap) // 2, top), ((W - 2 * pw - gap) // 2 + pw + gap, top)]
        label_h, label_dy = 150, ph + 18
        title_box = (W, 130, 100)
        name_pt, stats_pt, blind_pt = 44, 30, 64
    else:
        W, H, pw, ph, gap = 1080, 1920, 1000, 562, 0
        boxes = [(40, 300), (40, 300 + 562 + 220)]
        label_h, label_dy = 170, ph + 14
        title_box = (W, 200, 70)
        name_pt, stats_pt, blind_pt = 56, 40, 80

    # title band
    tlines = [(a.title, 52 if a.layout == "side" else 58, INK, True)]
    if a.prompt:
        tlines.append((f"“{a.prompt}”", 28 if a.layout == "side" else 32, DIM, False))
    text_png(str(tmp / "title.png"), title_box[0], title_box[1], tlines, bold, reg)

    # labels: real ones, and blind ones (A / B) when asked
    sides = [("left", a.left_name, a.left_stats), ("right", a.right_name, a.right_stats)]
    for key, name, stats in sides:
        lines = [(name, name_pt, INK, True)] + ([(stats, stats_pt, ACCENT_TEXT, False)] if stats else [])
        text_png(str(tmp / f"{key}.png"), pw, label_h, lines, bold, reg)
        text_png(str(tmp / f"{key}_blind.png"), pw, label_h, [("A" if key == "left" else "B", blind_pt, INK, True)], bold, reg)

    reveal = max(0.0, dur - a.blind) if a.blind else 0.0
    inputs = ["-f", "lavfi", "-i", f"color=c={BG}:s={W}x{H}:r={a.fps}:d={dur}"]
    inputs += ["-i", a.left, "-i", a.right, "-i", str(tmp / "title.png")]
    inputs += ["-i", str(tmp / "left.png"), "-i", str(tmp / "right.png")]
    inputs += ["-i", str(tmp / "left_blind.png"), "-i", str(tmp / "right_blind.png")]
    if a.music:
        inputs += ["-i", a.music]

    def panel(i):
        # fit, pad to the panel, same fps, hold the last frame if the clip is shorter than the film
        return (f"[{i}:v]fps={a.fps},scale={pw}:{ph}:force_original_aspect_ratio=decrease,"
                f"pad={pw}:{ph}:(ow-iw)/2:(oh-ih)/2:color={BG},setsar=1,"
                f"tpad=stop_mode=clone:stop_duration={dur},trim=duration={dur},setpts=PTS-STARTPTS[p{i}]")

    f = [panel(1), panel(2)]
    cur = "[0:v]"
    f.append(f"{cur}[3:v]overlay=0:{title_box[2]}[t]")
    cur = "[t]"
    for n, (x, y) in enumerate(boxes):
        if a.winner and ((a.winner == "left") == (n == 0)):
            frame = f"color=c={ACCENT}:s={pw + 12}x{ph + 12}:r={a.fps}:d={dur}"
            f.append(f"{frame}[fr{n}]")
            en = f":enable='gte(t,{reveal})'" if a.blind else ""
            f.append(f"{cur}[fr{n}]overlay={x - 6}:{y - 6}{en}[w{n}]")
            cur = f"[w{n}]"
        f.append(f"{cur}[p{n + 1}]overlay={x}:{y}[v{n}]")
        cur = f"[v{n}]"
        real, blind = 4 + n, 6 + n
        if a.blind:
            f.append(f"{cur}[{blind}:v]overlay={x}:{y + label_dy}:enable='lt(t,{reveal})'[b{n}]")
            f.append(f"[b{n}][{real}:v]overlay={x}:{y + label_dy}:enable='gte(t,{reveal})'[l{n}]")
        else:
            f.append(f"{cur}[{real}:v]overlay={x}:{y + label_dy}[l{n}]")
        cur = f"[l{n}]"
    f.append(f"{cur}format=yuv420p[out]")
    maps = ["-map", "[out]"]
    if a.music:
        f.append(f"[8:a]atrim=duration={dur},afade=t=out:st={max(0, dur - 1)}:d=1,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
        maps += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]

    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f), *maps,
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-r", str(a.fps), "-t", f"{dur}",
         "-movflags", "+faststart", a.out])
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{a.out}  {W}x{H}  {dur:.2f}s" + (f"  reveal at {reveal:.2f}s" if a.blind else ""))


if __name__ == "__main__":
    main()
