#!/usr/bin/env python3
"""Palette tools for a video moodboard. Needs Python 3 and Pillow (pip install pillow).

  extract IMAGE [--k 6] [--json]       dominant colours of a reference frame, as hex with % share
  check IMAGE... --hex 0F3B3F,E07A2E [--ref REF] [--max 15] [--json]
                                       how far a still's pixels sit from the board's hex set
                                       (mean CIE76 ΔE in Lab to the nearest board colour). With --ref
                                       the bar is the reference frame's own ΔE + 5 (use it for dark or
                                       high-key looks); without it, mean <= --max (15).

In the test behind the skill, the stills made without the palette line drifted furthest from the hex set.
"""
import argparse, json, math, random, sys

try:
    from PIL import Image
except ImportError:
    sys.exit("palette.py needs Pillow: pip install pillow")


def pixels(path, width=160):
    im = Image.open(path).convert("RGB")
    h = max(1, round(im.height * width / im.width))
    small = im.resize((width, h))
    get = getattr(small, "get_flattened_data", None) or small.getdata
    return list(get())


def to_lab(rgb):
    def lin(c):
        c /= 255.0
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    r, g, b = (lin(float(v)) for v in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def dist(a, b):
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(a, b)))


def hexify(rgb):
    return "#" + "".join(f"{int(round(v)):02X}" for v in rgb)


def parse_hex(s):
    out = []
    for h in s.replace("#", "").split(","):
        h = h.strip()
        if len(h) != 6:
            sys.exit(f"bad hex: {h}")
        out.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    return out


def extract(path, k, seed=7):
    px = pixels(path)
    lab = [to_lab(p) for p in px]
    rnd = random.Random(seed)
    # k-means++ seeding in Lab
    cents = [lab[rnd.randrange(len(lab))]]
    while len(cents) < k:
        d2 = [min(dist(p, c) ** 2 for c in cents) for p in lab]
        tot = sum(d2) or 1
        r, acc = rnd.random() * tot, 0
        for p, d in zip(lab, d2):
            acc += d
            if acc >= r:
                cents.append(p)
                break
    for _ in range(12):
        groups = [[] for _ in cents]
        for i, p in enumerate(lab):
            groups[min(range(len(cents)), key=lambda j: dist(p, cents[j]))].append(i)
        cents = [tuple(sum(lab[i][d] for i in g) / len(g) for d in range(3)) if g else cents[j]
                 for j, g in enumerate(groups)]
    res = []
    for g in groups:
        if not g:
            continue
        rgb = tuple(sum(px[i][d] for i in g) / len(g) for d in range(3))
        res.append({"hex": hexify(rgb), "share": round(len(g) / len(px), 3),
                    "lightness": round(sum(lab[i][0] for i in g) / len(g), 1)})
    return sorted(res, key=lambda r: -r["share"])


def mean_de(path, pal):
    ds = [min(dist(to_lab(p), c) for c in pal) for p in pixels(path)]
    return sum(ds) / len(ds), sum(d < 15 for d in ds) / len(ds)


def check(path, hexes, limit, ref=None):
    """Mean CIE76 ΔE from every pixel to its nearest board colour. With --ref (the reference frame the palette was
    taken from), the bar is the reference's own distance + 5: dark or high-key looks sit far from any hex even when
    they are right, and the reference shows how far is right."""
    pal = [to_lab(h) for h in hexes]
    mean, near = mean_de(path, pal)
    row = {"image": path, "mean_dE": round(mean, 1), "share_within_15": round(near, 3)}
    if ref:
        base, _ = mean_de(ref, pal)
        row.update({"ref": ref, "ref_mean_dE": round(base, 1), "target": round(base + 5, 1), "pass": mean <= base + 5})
    else:
        row.update({"target": limit, "pass": mean <= limit})
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract"); e.add_argument("image"); e.add_argument("--k", type=int, default=6); e.add_argument("--json", action="store_true")
    c = sub.add_parser("check"); c.add_argument("image", nargs="+"); c.add_argument("--hex", required=True)
    c.add_argument("--ref"); c.add_argument("--max", type=float, default=15.0); c.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd == "extract":
        res = extract(a.image, a.k)
        if a.json:
            print(json.dumps(res, indent=1))
        else:
            for r in res:
                print(f"{r['hex']}  {r['share']:6.1%}  L*{r['lightness']:5.1f}")
    else:
        rows = [check(p, parse_hex(a.hex), a.max, a.ref) for p in a.image]
        if a.json:
            print(json.dumps(rows, indent=1))
        else:
            for r in rows:
                base = f", reference {r['ref_mean_dE']:.1f}" if "ref" in r else ""
                print(f"{'PASS' if r['pass'] else 'FAIL'}  mean ΔE {r['mean_dE']:5.1f} (target ≤ {r['target']:g}{base}), "
                      f"{r['share_within_15']:.0%} of pixels within ΔE 15  {r['image']}")


if __name__ == "__main__":
    main()
