#!/usr/bin/env python3
"""make_tin_bot.py: draws the parts of a small robot as transparent PNG files, and writes the character file that
rigs them. It is the worked example for "bring your own art": one image per part, transparent background, one
scale, a pivot for every part, and the nine mouth shapes as separate images.

    python3 make_tin_bot.py [OUT_DIR]        # default: the folder this script is in

Standard library only. Every picture is drawn here, from distance functions, with 3x3 supersampling for smooth
edges. Pixels per unit is 2, so a 40-unit part is an 80-pixel PNG. Run it twice and the bytes are identical.
"""
from __future__ import annotations

import json
import math
import struct
import sys
import zlib
from pathlib import Path

PPU = 2          # pixels per unit
SS = 3           # supersamples per pixel side

STEEL, STEEL_DARK, STEEL_FAR = (143, 164, 184), (107, 127, 147), (96, 112, 128)
EDGE, ORANGE, LED, SCREEN, WHITE = (36, 42, 56), (255, 138, 61), (255, 215, 106), (30, 34, 48), (250, 248, 240)


def rrect(x0, y0, x1, y1, r):
    cx, cy, hx, hy = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 - r, (y1 - y0) / 2 - r
    def sd(x, y):
        qx, qy = abs(x - cx) - hx, abs(y - cy) - hy
        return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r
    return sd


def circle(cx, cy, r):
    return lambda x, y: math.hypot(x - cx, y - cy) - r


def capsule(ax, ay, bx, by, r):
    def sd(x, y):
        px, py, dx, dy = x - ax, y - ay, bx - ax, by - ay
        h = max(0.0, min(1.0, (px * dx + py * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - dx * h, py - dy * h) - r
    return sd


class Picture:
    """A w x h unit picture. Shapes are painted in order; each one is anti-aliased and blended over the last."""

    def __init__(self, w, h):
        self.w, self.h = int(w * PPU), int(h * PPU)
        self.px = [[0.0, 0.0, 0.0, 0.0] for _ in range(self.w * self.h)]

    def paint(self, sd, colour, grow=0.0, alpha=1.0):
        for j in range(self.h):
            for i in range(self.w):
                hit = 0
                for sj in range(SS):
                    for si in range(SS):
                        x, y = (i + (si + 0.5) / SS) / PPU, (j + (sj + 0.5) / SS) / PPU
                        hit += sd(x, y) <= grow
                cov = hit / (SS * SS) * alpha
                if cov:
                    p = self.px[j * self.w + i]
                    out_a = cov + p[3] * (1 - cov)
                    for c in range(3):
                        p[c] = (colour[c] * cov + p[c] * p[3] * (1 - cov)) / out_a
                    p[3] = out_a

    def shape(self, sd, colour, edge=EDGE, line=0.9):
        self.paint(sd, edge, grow=line)
        self.paint(sd, colour)

    def png(self) -> bytes:
        rows = []
        for j in range(self.h):
            row = bytearray([0])
            for i in range(self.w):
                r, g, b, a = self.px[j * self.w + i]
                row += bytes([round(r), round(g), round(b), round(a * 255)])
            rows.append(bytes(row))
        def chunk(tag, data):
            body = tag + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


def limb(w, h, body, r=None):
    pic = Picture(w, h)
    pic.shape(rrect(1.5, 1.5, w - 1.5, h - 1.5, r or min(w, h) / 2 - 1.5), body)
    pic.paint(rrect(w * 0.28, 4, w * 0.4, h - 4, 1), STEEL_DARK if body == STEEL else STEEL_FAR, alpha=0.5)
    return pic


def foot(body):
    pic = Picture(40, 16)
    pic.shape(rrect(1.5, 1.5, 38.5, 14.5, 6), body)
    pic.shape(rrect(1.5, 10, 38.5, 14.5, 2), ORANGE)
    return pic


def hand(body):
    pic = Picture(20, 22)
    pic.shape(circle(10, 9, 7.5), body)
    pic.shape(capsule(5, 14, 6, 20, 2.2), body)
    pic.shape(capsule(14, 14, 14, 20, 2.2), body)
    return pic


def head():
    pic = Picture(68, 78)
    pic.shape(capsule(34, 2, 34, 14, 1.2), EDGE, line=0.3)
    pic.shape(circle(34, 4, 3.4), ORANGE)
    pic.shape(rrect(2, 14, 66, 76, 14), STEEL)
    pic.shape(rrect(9, 24, 59, 62, 9), SCREEN, edge=STEEL_DARK)
    pic.paint(rrect(2, 54, 66, 76, 12), STEEL_DARK, alpha=0.45)
    return pic


def torso():
    pic = Picture(52, 72)
    pic.shape(rrect(1.5, 1.5, 50.5, 70.5, 12), STEEL)
    pic.shape(rrect(12, 14, 40, 40, 5), SCREEN, edge=STEEL_DARK)
    pic.paint(circle(26, 27, 5), LED)
    pic.shape(rrect(12, 48, 40, 54, 2), ORANGE)
    return pic


def pelvis():
    pic = Picture(34, 24)
    pic.shape(rrect(1.5, 1.5, 32.5, 22.5, 8), STEEL_DARK)
    return pic


def eye():
    pic = Picture(16, 16)
    pic.paint(circle(8, 8, 7.5), LED, alpha=0.35)
    pic.paint(circle(8, 8, 5.5), LED)
    pic.paint(circle(6.4, 6.4, 1.8), WHITE)
    return pic


# One LED mouth per viseme, 30 x 18 units. Wide and thin, tall and round: each one reads at a glance.
def mouth(kind):
    pic = Picture(30, 18)
    c = LED
    if kind == "rest":
        pic.paint(rrect(5, 8, 25, 10, 1), c)
    elif kind == "AI":
        pic.paint(rrect(6, 1.5, 24, 16.5, 5), c)
        pic.paint(rrect(9, 5, 21, 13, 3), SCREEN)
    elif kind == "E":
        pic.paint(rrect(2, 6, 28, 12, 2.5), c)
        pic.paint(rrect(5, 8, 25, 9.5, 0.6), SCREEN)
    elif kind == "O":
        pic.paint(circle(15, 9, 7.5), c)
        pic.paint(circle(15, 9, 3.8), SCREEN)
    elif kind == "U":
        pic.paint(circle(15, 9, 4.4), c)
    elif kind == "MBP":
        pic.paint(rrect(4, 7, 26, 11.5, 2), c)
    elif kind == "FV":
        pic.paint(rrect(4, 4, 26, 10, 2), c)
        pic.paint(rrect(7, 11, 23, 14.5, 1.5), ORANGE)
    elif kind == "L":
        pic.paint(rrect(4, 4, 26, 14, 3), c)
        pic.paint(capsule(15, 10, 15, 8, 3), ORANGE)
    else:
        pic.paint(rrect(4, 5, 26, 13, 3), c)
        pic.paint(rrect(7, 7.5, 23, 10.5, 1), SCREEN)
    return pic


VISEMES = ["rest", "AI", "E", "O", "U", "MBP", "FV", "L", "etc"]


def pictures() -> dict[str, Picture]:
    out = {"head": head(), "torso": torso(), "pelvis": pelvis(), "eye": eye()}
    for far, body in ((False, STEEL), (True, STEEL_FAR)):
        sfx = "_far" if far else ""
        out["thigh" + sfx], out["shin" + sfx], out["foot" + sfx] = limb(18, 40, body), limb(16, 36, body), foot(body)
        out["upper" + sfx], out["lower" + sfx], out["hand" + sfx] = limb(16, 40, body), limb(14, 36, body), hand(body)
    for v in VISEMES:
        out["mouth_" + v] = mouth(v)
    return out


def rest_image(name, x, y, w, h):
    return {"src": f"parts/{name}.png", "x": x, "y": y, "w": w, "h": h}


def character() -> dict:
    def part(pid, parent, pivot, z, image, **kw):
        out = {"id": pid, "parent": parent, "pivot": pivot, "z": z, "shapes": [], **kw}
        if image:
            out["image"] = image
        return out
    def limbs(s, dx, z, sfx):
        return [part(f"leg{s}_up", "hip", [dx, -68], z + 6, rest_image("thigh" + sfx, dx - 9, -72, 18, 40)),
                part(f"leg{s}_lo", f"leg{s}_up", [dx, -36], z + 5, rest_image("shin" + sfx, dx - 8, -40, 16, 36)),
                part(f"foot{s}", f"leg{s}_lo", [dx, -8], z + 4, rest_image("foot" + sfx, dx - 10, -16, 40, 16))]
    def arms(s, dx, z, sfx):
        return [part(f"arm{s}_up", "torso", [dx, -138], z, rest_image("upper" + sfx, dx - 8, -142, 16, 40)),
                part(f"arm{s}_lo", f"arm{s}_up", [dx, -104], z - 1, rest_image("lower" + sfx, dx - 7, -106, 14, 36)),
                part(f"hand{s}", f"arm{s}_lo", [dx, -72], z + 1, rest_image("hand" + sfx, dx - 10, -76, 20, 22))]
    mouth_cfg = {"kind": "images", "images": {v: rest_image("mouth_" + v, 0, -172, 30, 18) for v in VISEMES}}
    parts = [
        part("hip", None, [0, -70], 10, rest_image("pelvis", -17, -82, 34, 24)),
        *limbs("F", 4, 0, "_far"), *limbs("N", 0, 4, ""),
        part("torso", "hip", [0, -80], 11, rest_image("torso", -26, -150, 52, 72)),
        *arms("F", 5, 6, "_far"),
        part("head", "torso", [0, -148], 13, rest_image("head", -34, -226, 68, 78)),
        part("eyeN", "head", [10, -186], 15, rest_image("eye", 2, -194, 16, 16)),
        part("eyeF", "head", [28, -186], 15, rest_image("eye", 21, -193, 14, 14)),
        part("mouth", "head", [14, -163], 15, None, mouth=mouth_cfg),
        *arms("N", 0, 12, ""),
    ]
    palette = {"steel": "#8fa4b8", "edge": "#242a38", "ink": "#242a38", "orange": "#ff8a3d"}
    return {"$schema": "../schema/character.schema.json", "id": "tin-bot", "name": "Tin Bot (image parts)", "kind": "object", "version": 1,
            "palette": palette, "proportions": {"height": 226, "legLength": 70}, "blink": True, "parts": parts}


def write_all(out: Path) -> None:
    (out / "parts").mkdir(parents=True, exist_ok=True)
    for name, pic in pictures().items():
        (out / "parts" / f"{name}.png").write_bytes(pic.png())
    (out / "tin-bot.json").write_text(json.dumps(character(), indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    write_all(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent)
