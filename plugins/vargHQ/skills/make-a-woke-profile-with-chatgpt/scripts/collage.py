#!/usr/bin/env python3
"""Assemble the "I MADE ME WOKE" collage from a wokify.py output folder, sized for X.

  python3 collage.py wokify-out            # collage.jpg  2400x3000 (4:5, X shows it uncropped in the feed)
  python3 collage.py wokify-out --anim     # + collage.mp4 (1200x1500) and collage.gif (720x900, under X's 5 MB mobile cap)

GIF tiles (card, pet, home, social) animate in the MP4 and GIF; the JPG uses their first frame.
Needs Pillow; --anim also needs ffmpeg. Missing tiles are skipped and the rows close up.
"""
import argparse, glob, os, shutil, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageSequence

LABELS = {"before": "BEFORE", "friends": "MY FRIENDS", "me": "ME", "card": "MY CARD", "linkedin": "MY LINKEDIN",
          "figure": "MY FIGURE", "pet": "MY PET", "drink": "MY FAV DRINK", "home": "MY HOME",
          "social": "MY SOCIAL LIFE", "game": "MY FAVORITE GAME", "colleagues": "MY COLLEAGUES"}
ROWS = [["before", "friends"], ["me", "card", "linkedin"], ["figure", "pet", "drink", "home"], ["social", "game", "colleagues"]]
CROP = {"card": 0.8}                    # the card GIF has dark margins: crop to the card
TOP = {"social", "colleagues"}          # labels top-left where the bottom has captions or a toolbar
W, H, P, G, HEAD, FOOT = 2400, 3000, 36, 14, 210, 76
BG = (17, 17, 17)
FONTS = {"black": ["Montserrat-Black.ttf", "Arial Black.ttf", "DejaVuSans-Bold.ttf"],
         "bold": ["Montserrat-Bold.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]}
DIRS = [os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts/Supplemental",
        "/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/TTF", "C:/Windows/Fonts"]


def font(kind, size):
    for name in FONTS[kind]:
        for d in DIRS:
            if os.path.exists(f"{d}/{name}"):
                return ImageFont.truetype(f"{d}/{name}", size)
    return ImageFont.load_default(size)


def find(out, tid):
    for ext in ("gif", "png", "jpg", "jpeg", "webp"):   # a GIF wins over its still
        hits = glob.glob(f"{out}/{tid}.{ext}")
        if hits:
            return hits[0]


def frames(path, asp):
    im = Image.open(path)
    fr = [(f.convert("RGB"), f.info.get("duration", 100)) for f in ImageSequence.Iterator(im)] if path.endswith(".gif") else [(im.convert("RGB"), 0)]
    if asp:
        out = []
        for x, d in fr:
            cw = min(x.width, round(x.height * asp)); l = (x.width - cw) // 2
            out.append((x.crop((l, 0, l + cw, x.height)), d))
        fr = out
    return fr


def fit(im, w, h):
    k = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * k)), max(h, round(im.height * k))), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out"); ap.add_argument("--anim", action="store_true")
    ap.add_argument("--title", default="I MADE ME WOKE", help="the last word gets the Pride-stripe fill")
    ap.add_argument("--footer", default="1 selfie  ·  11 prompts  ·  GPT Image 2.6")
    a = ap.parse_args()
    src = {t: frames(p, CROP.get(t)) for t in LABELS if (p := find(a.out, t))}
    if "before" not in src:
        sys.exit(f"no before.* in {a.out}: run wokify.py first")
    rows = [[t for t in r if t in src] for r in ROWS]
    rows = [r for r in rows if r]
    print("tiles:", ", ".join(t for r in rows for t in r))

    cw = W - 2 * P
    nat = []
    for r in rows:
        asp = [src[t][0][0].width / src[t][0][0].height for t in r]
        nat.append((asp, (cw - G * (len(r) - 1)) / sum(asp)))
    s = (H - P - HEAD - FOOT - G * (len(rows) - 1)) / sum(h for _, h in nat)   # stretch rows to fill 4:5 exactly
    layout, y = [], P + HEAD
    for ri, (r, (asp, h)) in enumerate(zip(rows, nat)):
        rh = round(h * s) if ri < len(rows) - 1 else H - FOOT - y
        x = P
        for i, t in enumerate(r):
            w = round(asp[i] * h) if i < len(r) - 1 else P + cw - x
            layout.append((t, x, y, w, rh)); x += w + G
        y += rh + G

    lab = font("black", 34)
    def label(tile, t):
        d = ImageDraw.Draw(tile, "RGBA"); text = LABELS[t]; tw = d.textlength(text, font=lab)
        ly = 16 if t in TOP else tile.height - 16 - 58
        d.rounded_rectangle([16, ly, 16 + tw + 52, ly + 58], radius=29, fill=(17, 17, 17, 230))
        d.text((16 + 26, ly + 29), text, font=lab, fill="white", anchor="lm")
        return tile

    def base():
        c = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(c)
        big = font("black", 168)
        head, _, last = a.title.rpartition(" ")
        head = head + " " if head else ""
        wa, wb = d.textlength(head, font=big), d.textlength(last, font=big)
        k = min(1, (W - 2 * P) / (wa + wb)); big = font("black", int(168 * k))
        wa, wb = d.textlength(head, font=big), d.textlength(last, font=big)
        x0 = (W - wa - wb) / 2
        top, bot = big.getbbox("IMADEWOKE")[1], big.getbbox("IMADEWOKE")[3]
        y0 = P + (HEAD - 24 - (bot - top)) / 2 - top
        d.text((x0, y0), head, font=big, fill="white")
        mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).text((x0 + wa, y0), last, font=big, fill=255)
        st = Image.new("RGB", (W, H), BG); sd = ImageDraw.Draw(st)
        for i, col in enumerate([(228, 3, 3), (255, 140, 0), (255, 237, 0), (0, 128, 38), (0, 77, 255), (117, 7, 135)]):
            sd.rectangle([0, y0 + top + (bot - top) * i / 6, W, y0 + top + (bot - top) * (i + 1) / 6 + 1], fill=col)
        c.paste(st, (0, 0), mask)
        d.text((W / 2, H - FOOT / 2 - 2), a.footer, font=font("bold", 34), fill=(150, 150, 150), anchor="mm")
        return c

    tf = {t: [(label(fit(im, w, h), t), d) for im, d in src[t]] for t, x, y, w, h in layout}
    pos = {t: (x, y) for t, x, y, w, h in layout}
    def compose(ms):
        c = base()
        for t, fr in tf.items():
            if len(fr) == 1:
                c.paste(fr[0][0], pos[t]); continue
            tt = ms % sum(d for _, d in fr)
            for im, d in fr:
                if tt < d:
                    c.paste(im, pos[t]); break
                tt -= d
        return c

    jpg = os.path.join(a.out, "collage.jpg")
    compose(0).save(jpg, quality=90, optimize=True)
    print(jpg, os.path.getsize(jpg) // 1024, "KB", f"{W}x{H}")
    if a.anim:
        if not shutil.which("ffmpeg"):
            sys.exit("--anim needs ffmpeg")
        fd = os.path.join(a.out, "_frames"); shutil.rmtree(fd, ignore_errors=True); os.makedirs(fd)
        fps, sec = 25, 4
        for i in range(fps * sec):
            compose(i * 1000 / fps).resize((1200, 1500), Image.LANCZOS).save(f"{fd}/{i:04d}.png")
        mp4, gif = os.path.join(a.out, "collage.mp4"), os.path.join(a.out, "collage.gif")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{fd}/%04d.png", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart", mp4], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{fd}/%04d.png", "-vf",
                        "fps=8,scale=720:900:flags=lanczos,split[a][b];[a]palettegen=max_colors=256:stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle",
                        "-loop", "0", gif], check=True)
        shutil.rmtree(fd)
        for f in (mp4, gif):
            print(f, os.path.getsize(f) // 1024, "KB")


if __name__ == "__main__":
    main()
