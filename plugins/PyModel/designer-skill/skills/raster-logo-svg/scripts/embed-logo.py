#!/usr/bin/env python3
"""Wrap a raster logo in a self-contained SVG (base64 data URI)."""
from __future__ import annotations

import argparse
import base64
import mimetypes
import subprocess
from pathlib import Path
from xml.sax.saxutils import quoteattr

MIME = {
    ".webp": "image/webp",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
}


def dimensions(path: Path) -> tuple[int, int]:
    # `[0]` reads only the first frame, so animated GIF/WebP report one size.
    try:
        out = subprocess.run(
            ["magick", "identify", "-format", "%w %h\n", f"{path}[0]"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise SystemExit("ImageMagick 7 (`magick`) is required: brew install imagemagick")
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"magick could not read {path}: {error.stderr.strip() or error}")
    try:
        w, h = out.stdout.splitlines()[0].split()
        return int(w), int(h)
    except (IndexError, ValueError):
        raise SystemExit(f"unexpected magick output for {path}: {out.stdout!r}")


def mime_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in MIME:
        return MIME[ext]
    guessed, _ = mimetypes.guess_type(path.name)
    if not guessed:
        raise SystemExit(f"unsupported image type: {ext or path.name}")
    return guessed


def embed(input_path: Path, output_path: Path, label: str) -> None:
    mime = mime_for(input_path)
    w, h = dimensions(input_path)
    data = base64.b64encode(input_path.read_bytes()).decode("ascii")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f"role=\"img\" aria-label={quoteattr(label)}>\n"
        f'  <image width="{w}" height="{h}" href="data:{mime};base64,{data}"/>\n'
        f"</svg>\n"
    )
    output_path.write_text(svg, encoding="utf-8")
    print(f"wrote {output_path} ({output_path.stat().st_size} bytes, {w}x{h})")


def main() -> None:
    p = argparse.ArgumentParser(description="Embed a raster logo in SVG")
    p.add_argument("input", type=Path, help="source image (.webp, .png, .jpg)")
    p.add_argument("-o", "--output", type=Path, help="output .svg (default: same stem as input)")
    p.add_argument("-l", "--label", default="", help="aria-label (default: input stem)")
    p.add_argument("-f", "--force", action="store_true", help="overwrite an existing output file")
    args = p.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"not found: {args.input}")
    out = args.output or args.input.with_suffix(".svg")
    if out.exists() and out.resolve() == args.input.resolve():
        raise SystemExit(f"refusing to overwrite the input image {args.input}")
    if out.exists() and not args.force:
        raise SystemExit(f"{out} exists; pass --force to overwrite it")
    label = args.label or out.stem.replace("-", " ")
    embed(args.input, out, label)


if __name__ == "__main__":
    main()
