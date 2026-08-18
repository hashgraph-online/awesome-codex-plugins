#!/usr/bin/env python3
"""Wrap a raster logo in a self-contained SVG (base64 data URI)."""
from __future__ import annotations

import argparse
import base64
import mimetypes
import subprocess
import sys
from pathlib import Path

MIME = {
    ".webp": "image/webp",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
}


def dimensions(path: Path) -> tuple[int, int]:
    out = subprocess.run(
        ["magick", "identify", "-format", "%w %h", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    w, h = out.stdout.strip().split()
    return int(w), int(h)


def mime_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in MIME:
        return MIME[ext]
    guessed, _ = mimetypes.guess_type(path.name)
    if not guessed:
        raise SystemExit(f"unsupported image type: {ext or path.name}")
    return guessed


def embed(input_path: Path, output_path: Path, label: str) -> None:
    w, h = dimensions(input_path)
    data = base64.b64encode(input_path.read_bytes()).decode("ascii")
    mime = mime_for(input_path)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{label}">\n'
        f'  <image width="{w}" height="{h}" href="data:{mime};base64,{data}"/>\n'
        f"</svg>\n"
    )
    output_path.write_text(svg)
    print(f"wrote {output_path} ({output_path.stat().st_size} bytes, {w}x{h})")


def main() -> None:
    p = argparse.ArgumentParser(description="Embed a raster logo in SVG")
    p.add_argument("input", type=Path, help="source image (.webp, .png, .jpg)")
    p.add_argument("-o", "--output", type=Path, help="output .svg (default: same stem as input)")
    p.add_argument("-l", "--label", default="", help="aria-label (default: input stem)")
    args = p.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"not found: {args.input}")
    out = args.output or args.input.with_suffix(".svg")
    label = args.label or out.stem.replace("-", " ")
    embed(args.input, out, label)


if __name__ == "__main__":
    main()
