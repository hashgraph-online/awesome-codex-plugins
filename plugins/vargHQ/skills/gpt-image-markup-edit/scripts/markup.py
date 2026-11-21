#!/usr/bin/env python3
"""Draw a markup layer for a GPT Image 2.6 markup-guided edit. Needs Python 3 and Pillow (pip install pillow).

  markup.py SOURCE SPEC.json [-o markup.png] [--preview preview.png] [--mask mask.png]

SOURCE is the image you will edit. The markup is a transparent PNG of exactly the same size with only
your circles, arrows, boxes and short notes on it (fal: "Transparent PNG containing only annotations ...
that guide the edit of the first image"). The preview puts the markup on top of SOURCE so you can check
it. --mask also writes a black-and-white mask of the filled shapes (fal mask_url: white = edit,
black = keep), for when you want a mask instead of markup. The script prints one prompt line per
shape, written by colour, to paste into the edit prompt.

SPEC.json:
{
  "units": "px",                 # or "fraction" (0-1 of width/height); auto when every number <= 1
  "width": 10,                   # stroke width in px (default: 1.3% of the short side, at least 4)
  "shapes": [
    {"type": "ellipse", "box": [x0, y0, x1, y1], "color": "red",  "label": "put a Santa hat on the cat"},
    {"type": "rect",    "box": [x0, y0, x1, y1], "color": "blue", "label": "...", "note": "GIFT"},
    {"type": "arrow",   "from": [x, y], "to": [x, y], "color": "green", "label": "move the lamp here"},
    {"type": "text",    "at": [x, y], "text": "NO TEXT", "color": "yellow"}
  ]
}
"label" goes into the prompt only. "note" (1-3 words) is also drawn on the markup next to the shape.
Colours: red, blue, green, yellow, magenta, orange, cyan, white, black, or "#RRGGBB".
"""
import argparse, json, math, os, sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("markup.py needs Pillow: pip install pillow")

COLORS = {
    "red": (255, 30, 30), "blue": (20, 90, 255), "green": (0, 200, 80), "yellow": (255, 215, 0),
    "magenta": (255, 0, 200), "orange": (255, 140, 0), "cyan": (0, 210, 255),
    "white": (255, 255, 255), "black": (0, 0, 0),
}
SHAPE_WORD = {"ellipse": "circle", "rect": "box", "arrow": "arrow", "text": "note"}
FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def rgb(name):
    if isinstance(name, str) and name.startswith("#") and len(name) == 7:
        return tuple(int(name[i:i + 2], 16) for i in (1, 3, 5))
    if name in COLORS:
        return COLORS[name]
    sys.exit(f"unknown colour {name!r}: use {', '.join(COLORS)} or #RRGGBB")


def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def numbers(shape):
    out = []
    for k in ("box", "from", "to", "at"):
        out += list(shape.get(k, []))
    return out


def scale(shape, w, h, frac):
    if not frac:
        return shape
    s = dict(shape)
    for k in ("box", "from", "to", "at"):
        if k in s:
            v = s[k]
            s[k] = [v[i] * (w if i % 2 == 0 else h) for i in range(len(v))]
    return s


def arrow(draw, a, b, color, width):
    draw.line([tuple(a), tuple(b)], fill=color, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    head = max(width * 4, 18)
    left = (b[0] - head * math.cos(ang - math.pi / 6), b[1] - head * math.sin(ang - math.pi / 6))
    right = (b[0] - head * math.cos(ang + math.pi / 6), b[1] - head * math.sin(ang + math.pi / 6))
    draw.polygon([tuple(b), left, right], fill=color)


def write(draw, xy, text, color, size, w, h):
    f = font(size)
    x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=f, stroke_width=max(2, size // 10))
    x = min(max(0, xy[0]), w - (x1 - x0))
    y = min(max(0, xy[1]), h - (y1 - y0))
    draw.text((x, y), text, font=f, fill=color, stroke_width=max(2, size // 10), stroke_fill=(255, 255, 255))


def main():
    ap = argparse.ArgumentParser(description="Markup layer for a GPT Image 2.6 markup-guided edit.")
    ap.add_argument("source")
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", help="markup PNG (default: <source>_markup.png)")
    ap.add_argument("--preview", help="source + markup composite (default: <source>_markup_preview.png)")
    ap.add_argument("--mask", help="also write a mask PNG: filled shapes white on black")
    args = ap.parse_args()

    src = Image.open(args.source)
    w, h = src.size
    spec = json.load(open(args.spec))
    shapes = spec.get("shapes", [])
    if not shapes:
        sys.exit("spec has no shapes")
    nums = [n for s in shapes for n in numbers(s)]
    frac = spec.get("units") == "fraction" or (spec.get("units") is None and nums and max(nums) <= 1)
    width = int(spec.get("width") or max(4, round(min(w, h) * 0.013)))
    note_size = int(spec.get("note_size") or max(18, round(min(w, h) * 0.04)))

    base, _ = os.path.splitext(args.source)
    out = args.out or base + "_markup.png"
    preview = args.preview or base + "_markup_preview.png"

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    mask = Image.new("L", (w, h), 0) if args.mask else None
    md = ImageDraw.Draw(mask) if mask else None
    lines = []

    for raw in shapes:
        s = scale(raw, w, h, frac)
        kind = s.get("type", "ellipse")
        name = s.get("color", "red")
        c = rgb(name) + (255,)
        if kind in ("ellipse", "rect"):
            x0, y0, x1, y1 = s["box"]
            box = [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]
            (d.ellipse if kind == "ellipse" else d.rectangle)(box, outline=c, width=width)
            if md:
                (md.ellipse if kind == "ellipse" else md.rectangle)(box, fill=255)
            anchor = (box[0], box[1] - note_size - width)
        elif kind == "arrow":
            arrow(d, s["from"], s["to"], c, width)
            anchor = (s["from"][0], s["from"][1] - note_size - width)
        elif kind == "text":
            write(d, s["at"], s["text"], c, note_size, w, h)
            anchor = None
        else:
            sys.exit(f"unknown shape type {kind!r}: use ellipse, rect, arrow or text")
        if s.get("note") and anchor:
            write(d, anchor, s["note"], c, note_size, w, h)
        if s.get("label"):
            word = name if not name.startswith("#") else f"{name} colour"
            lines.append(f"{word.capitalize()} {SHAPE_WORD.get(kind, kind)}: {s['label'].rstrip('.')}.")

    layer.save(out)
    comp = src.convert("RGBA")
    comp.alpha_composite(layer)
    comp.convert("RGB").save(preview)
    if mask:
        mask.save(args.mask)

    check = Image.open(out)
    assert check.size == (w, h) and check.mode == "RGBA"
    print(f"markup   {out} ({w}x{h}, RGBA, transparent outside the marks)")
    print(f"preview  {preview}")
    if mask:
        print(f"mask     {args.mask} (white = edit, black = keep)")
    if lines:
        print("prompt:")
        for line in lines:
            print("  " + line)
        print("  Change nothing outside the marks.")


if __name__ == "__main__":
    main()
