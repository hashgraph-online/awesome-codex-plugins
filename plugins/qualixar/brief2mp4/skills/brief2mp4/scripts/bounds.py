#!/usr/bin/env python3
"""bounds.py: measure where content sits in a still, and check it against margins or safe zones.

Uses only the Python standard library, so it runs wherever Python 3.8+ does. Reads the 8-bit
PNGs that contact_sheet.sh and ffmpeg write.

  python3 bounds.py still.png --bg "#101114"
      prints the bounding box of every pixel that differs from the background
  python3 bounds.py still.png --bg "#F4F1EA" --region 0,700,1920,1080
      only look inside x0,y0,x1,y1 (for example the band where a label sits)
  python3 bounds.py still.png --bg "#101114" --safe top=288,bottom=672,left=64,right=192
      also checks the box against safe zones (vertical Shorts and Reels)
  python3 bounds.py still.png --bg "#F2EDE4" --margin 96,54
      checks a left/right and top/bottom safe margin (5% at 1920x1080)

Prints one JSON object. Exit 0 when the box is inside the zones (or none were given), 1 otherwise.
A box height is a good proxy for text height when you measure a single line. It measures ink, not font-size: a line without descenders (no g, j, p, q, y) is shorter than its font-size, a line with them is taller than its cap height. Compare like with like, or check the CSS for font-size.

Measuring one element (a moving dot, one label): pass a --region that contains only that element,
then read its box centre: cx = (x0 + x1) / 2, cy = (y0 + y1) / 2. For easing, measure the centre at
the start, at the end and at the time the brief names: covered = (c_t - c_start) / (c_end - c_start).
For an orbit, the angle is atan2(cy - circle_y, cx - circle_x) at each still.
"""
import argparse
import json
import struct
import sys
import zlib


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    pos, idat, w = 8, [], None
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or ctype not in (0, 2, 4, 6) or interlace:
                raise ValueError("only 8-bit, non-interlaced grey, RGB or RGBA PNGs are supported")
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
        pos += 12 + length
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    return w, h, channels, unfilter(zlib.decompress(b"".join(idat)), w, h, channels)


def paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def unfilter(raw, w, h, bpp):
    stride, out, prev, i = w * bpp, [], bytearray(w * bpp), 0
    for _ in range(h):
        ftype, line = raw[i], bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b, c = prev[x], (prev[x - bpp] if x >= bpp else 0)
            if ftype == 1:
                line[x] = (line[x] + a) & 255
            elif ftype == 2:
                line[x] = (line[x] + b) & 255
            elif ftype == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif ftype == 4:
                line[x] = (line[x] + paeth(a, b, c)) & 255
        out.append(bytes(line))
        prev = line
    return out


def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[k:k + 2], 16) for k in (0, 2, 4))


def bbox(rows, w, h, ch, bg, tol, region):
    x0r, y0r, x1r, y1r = region or (0, 0, w, h)
    found = [w, h, -1, -1]
    for y in range(max(0, y0r), min(h, y1r)):
        row = rows[y]
        for x in range(max(0, x0r), min(w, x1r)):
            px = row[x * ch:x * ch + ch]
            rgb = (px[0],) * 3 if ch <= 2 else px[:3]
            if max(abs(rgb[k] - bg[k]) for k in range(3)) > tol:
                found = [min(found[0], x), min(found[1], y), max(found[2], x), max(found[3], y)]
    return None if found[2] < 0 else found


def parse_zones(args, w, h):
    zones = {}
    if args.safe:
        for part in args.safe.split(","):
            key, val = part.split("=")
            zones[key.strip()] = int(val)
    if args.margin:
        mx, my = (int(v) for v in args.margin.split(","))
        zones = {"left": mx, "right": mx, "top": my, "bottom": my, **zones}
    return {"left": zones.get("left", 0), "right": w - zones.get("right", 0),
            "top": zones.get("top", 0), "bottom": h - zones.get("bottom", 0)} if zones else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("png")
    ap.add_argument("--bg", required=True, help="background colour as #rrggbb")
    ap.add_argument("--tol", type=int, default=24, help="per-channel difference that counts as content (default 24)")
    ap.add_argument("--region", help="x0,y0,x1,y1 to search inside")
    ap.add_argument("--safe", help="safe zones in px, e.g. top=288,bottom=672,left=64,right=192")
    ap.add_argument("--margin", help="symmetric margins in px as X,Y, e.g. 96,54")
    args = ap.parse_args()
    w, h, ch, rows = read_png(args.png)
    region = tuple(int(v) for v in args.region.split(",")) if args.region else None
    box = bbox(rows, w, h, ch, hex_rgb(args.bg), args.tol, region)
    result = {"file": args.png, "size": [w, h], "box": None, "inside": None}
    if box:
        result["box"] = {"x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3],
                         "width": box[2] - box[0] + 1, "height": box[3] - box[1] + 1}
    zone = parse_zones(args, w, h)
    if zone and box:
        result["zone"] = zone
        result["inside"] = (box[0] >= zone["left"] and box[2] < zone["right"]
                            and box[1] >= zone["top"] and box[3] < zone["bottom"])
    print(json.dumps(result))
    return 1 if result["inside"] is False else 0


if __name__ == "__main__":
    sys.exit(main())
