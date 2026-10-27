#!/usr/bin/env python3
"""Real-frame contact sheet of a reference (never design from memory).

  python3 ref_frames.py <youtube-url | .mp4 url | image urls/paths...> --name NAME [--out refs/frames] [--n 24]

YouTube / mp4: yt-dlp (480p) + ffmpeg → N frames tiled 6 wide.  Needs yt-dlp and ffmpeg on PATH, or $YTDLP / $FF
  (pro-motion projects have both under tools/: FF=tools/node_modules/ffmpeg-static/ffmpeg YTDLP=tools/yt-dlp).
If yt-dlp asks for login ("Sign in to confirm you're not a bot") or a tool is missing, falls back to the PUBLIC
  thumbnails i.ytimg.com/vi/<id>/{maxresdefault,hq1,hq2,hq3}.jpg — 4 real frames, no login. Says which path it took.
Images (Behance CDN mir-s3-cdn-cf.behance.net, App Store art, local screenshots): downloaded/tiled as given.
  Behance pages block curl: list the CDN urls from an already-open tab with the browser javascript tool, then pass them here.
Writes NAME_sheet.jpg plus the single frames in <out>/NAME/. Hand the sheet to a cheap image-reader subagent, not the main session.
"""
import argparse, os, pathlib, re, shutil, subprocess, sys
from PIL import Image

UA = {"User-Agent": "Mozilla/5.0"}


def get(url, dst):
    # curl, not urllib: python.org builds on macOS often lack CA certs (CERTIFICATE_VERIFY_FAILED)
    subprocess.run(["curl", "-sfL", "-A", UA["User-Agent"], "-o", str(dst), url], check=True, timeout=60)


def tile(paths, out, cols=6, h=300):
    ims = [Image.open(p).convert("RGB") for p in paths]
    ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
    w = max(i.width for i in ims)
    cols = min(cols, len(ims))
    rows = -(-len(ims) // cols)
    sheet = Image.new("RGB", (w * cols, h * rows), (0, 0, 0))
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % cols) * w, (k // cols) * h))
    sheet.save(out, quality=88)
    return out


def yt_id(u):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})", u)
    return m.group(1) if m else None


def video(url, d, n):
    y, ff = os.environ.get("YTDLP") or shutil.which("yt-dlp"), os.environ.get("FF") or shutil.which("ffmpeg")
    if not ff or (not y and not url.endswith(".mp4")):
        return None, "missing yt-dlp/ffmpeg"
    mp4 = d / "clip.mp4"
    if url.endswith(".mp4"):
        get(url, mp4)
    else:
        r = subprocess.run([y, "-q", "--no-warnings", "-f", "bv*[height<=480][ext=mp4]/b[height<=480]/worst", "-o", str(mp4), url],
                           capture_output=True, text=True)
        if r.returncode or not mp4.exists():
            return None, ("login required" if "Sign in" in r.stderr else r.stderr.strip()[-160:])
    probe = subprocess.run([ff, "-i", str(mp4)], capture_output=True, text=True).stderr
    hh, mm, ss = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe).groups()
    dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
    subprocess.run([ff, "-loglevel", "error", "-y", "-i", str(mp4), "-vf", f"fps={n}/{dur},scale=-2:300", str(d / "f%03d.jpg")], check=True)
    return sorted(d.glob("f*.jpg")), f"{len(list(d.glob('f*.jpg')))} frames from {dur:.0f}s video"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("src", nargs="+"); p.add_argument("--name", required=True)
    p.add_argument("--out", default="refs/frames"); p.add_argument("--n", type=int, default=24)
    a = p.parse_args()
    d = pathlib.Path(a.out) / a.name
    d.mkdir(parents=True, exist_ok=True)
    frames, how = None, ""
    first = a.src[0]
    if len(a.src) == 1 and (yt_id(first) or first.endswith(".mp4")):
        frames, how = video(first, d, a.n)
        if not frames and yt_id(first):
            vid, frames = yt_id(first), []
            for k in ("maxresdefault", "hq1", "hq2", "hq3"):
                try:
                    p = d / f"{vid}_{k}.jpg"
                    get(f"https://i.ytimg.com/vi/{vid}/{k}.jpg", p)
                    im = Image.open(p)
                    if k.startswith("hq") and im.width * 3 == im.height * 4:   # 4:3 thumb letterboxing a 16:9 frame
                        bar = (im.height - im.width * 9 // 16) // 2
                        im.crop((0, bar, im.width, im.height - bar)).save(p, quality=92)
                    frames.append(p)
                except Exception:
                    pass
            how = f"video path failed ({how}) → {len(frames)} public ytimg thumbnails"
    else:
        frames = []
        for i, s in enumerate(a.src):
            dst = d / f"{i:02d}{pathlib.Path(s.split('?')[0]).suffix or '.jpg'}"
            get(s, dst) if s.startswith("http") else shutil.copy(s, dst)
            frames.append(dst)
        how = f"{len(frames)} images"
    if not frames:
        sys.exit(f"no frames: {how}")
    print("wrote", tile(frames, pathlib.Path(a.out) / f"{a.name}_sheet.jpg"), "·", how)


if __name__ == "__main__":
    main()
