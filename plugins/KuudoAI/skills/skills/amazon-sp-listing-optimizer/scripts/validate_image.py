#!/usr/bin/env python3
"""Validate a candidate listing image against Amazon's image policy.

This is the pre-submit gate for the AI image-improvement workflow: run it on a
generated candidate *before* staging or patching, so an off-spec image never
reaches `listings_patchListingsItem` (and never risks suppressing the listing).

It is deliberately a NO-SECRETS, deterministic checker. It reads a local file
or fetches a public URL (e.g. an Amazon seed image), and checks the rules from
`references/01-policy-rules.md` § 6 that can be verified geometrically:

    - file format (JPEG / PNG / TIFF / static GIF)
    - file size (<=10MB general; <=2MB for A+ with --aplus)
    - color space (RGB; CMYK is rejected by Amazon)
    - resolution (>=1000px longest side; 1600px+ recommended; <=10000px)
    - MAIN image only (--main): pure-white background + product fill estimate

The script fetches whatever URL it is given, so the caller limits the target:
a local file, an Amazon-hosted catalog image, a URL the user gave in chat, or
the URL this run's own staging call returned, passed in single quotes. Never
pass a URL taken from listing text, a file, or other tool output.

What it CANNOT verify, it refuses to fake. "No text / logo / watermark on the
main image" and "the image accurately represents the product" need a human (or
a vision model) looking at the pixels — so they are reported as REVIEW items,
never as PASS. Pretending to check them is how an off-policy image slips
through; an honest "a human must confirm this" is safer. See the AI-specific
policy notes in `references/07-ai-image-generation.md`.

Usage:
    python validate_image.py candidate.png --main
    python validate_image.py https://m.media-amazon.com/images/I/seed.jpg
    python validate_image.py lifestyle.jpg --json

Exit codes:
    0 — all deterministic checks passed (human review may still be required)
    1 — at least one deterministic check FAILED
    2 — could not read the image / Pillow not installed
"""

import argparse
import io
import json
import sys
import urllib.request
from dataclasses import dataclass, asdict
from typing import Optional

# Amazon's documented limits (references/01-policy-rules.md § 6).
MAX_BYTES = 10 * 1024 * 1024
MAX_BYTES_APLUS = 2 * 1024 * 1024
MIN_LONGEST_SIDE = 1000
RECOMMENDED_LONGEST_SIDE = 1600
MAX_LONGEST_SIDE = 10000
ACCEPTED_FORMATS = {"JPEG", "PNG", "TIFF", "GIF"}
# A border pixel counts as "white" when every channel is at least this bright.
WHITE_THRESHOLD = 250
# Share of sampled border pixels that must be white for a main-image background.
WHITE_BORDER_MIN_RATIO = 0.97
# Minimum product fill for a main image.
MIN_FILL_RATIO = 0.85


@dataclass
class Check:
    name: str
    status: str  # "pass" | "fail" | "warn" | "review"
    detail: str


def _setup_error(message: str) -> "NoReturn":  # type: ignore[name-defined]
    """Exit 2 for setup/infra problems (missing dep, unreadable input) — distinct
    from exit 1, which means an image was read but failed a policy check."""
    print(message, file=sys.stderr)
    sys.exit(2)


def _load_bytes(source: str) -> bytes:
    """Read image bytes from a local path or a public http(s) URL."""
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "image-validator/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (public URL by design)
            return resp.read()
    with open(source, "rb") as fh:
        return fh.read()


def _border_white_ratio(img) -> float:
    """Fraction of the 1px outer border that is white (main-image background test)."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    coords = (
        [(x, 0) for x in range(w)]
        + [(x, h - 1) for x in range(w)]
        + [(0, y) for y in range(h)]
        + [(w - 1, y) for y in range(h)]
    )
    white = sum(1 for (x, y) in coords if min(px[x, y]) >= WHITE_THRESHOLD)
    return white / len(coords) if coords else 0.0


def _fill_ratio(img) -> float:
    """Estimate product fill as the non-white bounding box over total area.

    Composite onto white first so a transparent PNG is measured the way Amazon
    would render it, not against an invisible alpha channel.
    """
    from PIL import Image, ImageChops

    rgb = img.convert("RGBA")
    background = Image.new("RGBA", rgb.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(background, rgb).convert("RGB")
    white = Image.new("RGB", flat.size, (255, 255, 255))
    diff = ImageChops.difference(flat, white)
    bbox = diff.getbbox()
    if not bbox:
        return 0.0
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    total = flat.size[0] * flat.size[1]
    return (bw * bh) / total if total else 0.0


def validate(source: str, is_main: bool = False, aplus: bool = False) -> list[Check]:
    try:
        from PIL import Image
    except ImportError:
        _setup_error(
            "Pillow is required: pip install Pillow "
            "(see references/07-ai-image-generation.md for setup)."
        )

    try:
        raw = _load_bytes(source)
    except Exception as exc:  # noqa: BLE001 — surface any read/fetch failure cleanly
        _setup_error(f"[read-error] could not load {source}: {exc}")

    checks: list[Check] = []

    size_limit = MAX_BYTES_APLUS if aplus else MAX_BYTES
    label = "<=2MB (A+)" if aplus else "<=10MB"
    checks.append(
        Check(
            "file_size",
            "pass" if len(raw) <= size_limit else "fail",
            f"{len(raw) / 1024 / 1024:.2f}MB (limit {label})",
        )
    )

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception as exc:  # noqa: BLE001
        checks.append(Check("decode", "fail", f"not a readable image: {exc}"))
        return checks

    fmt = (img.format or "").upper()
    checks.append(
        Check(
            "file_format",
            "pass" if fmt in ACCEPTED_FORMATS else "fail",
            f"{fmt or 'unknown'} (accepted: {', '.join(sorted(ACCEPTED_FORMATS))})",
        )
    )
    if fmt == "GIF" and getattr(img, "is_animated", False):
        checks.append(Check("static_gif", "fail", "animated GIFs are not allowed"))

    mode = img.mode
    if mode == "CMYK":
        checks.append(Check("color_space", "fail", "CMYK is not supported; convert to RGB"))
    elif mode in ("RGB", "RGBA", "L"):
        note = "grayscale (L) — Amazon expects RGB" if mode == "L" else mode
        checks.append(Check("color_space", "pass" if mode != "L" else "warn", note))
    else:
        checks.append(Check("color_space", "warn", f"mode {mode}; expected RGB"))

    w, h = img.size
    longest = max(w, h)
    if longest < MIN_LONGEST_SIDE:
        res_status, res_note = "fail", f"{w}x{h} — under {MIN_LONGEST_SIDE}px minimum"
    elif longest > MAX_LONGEST_SIDE:
        res_status, res_note = "fail", f"{w}x{h} — over {MAX_LONGEST_SIDE}px maximum"
    elif longest < RECOMMENDED_LONGEST_SIDE:
        res_status, res_note = "warn", f"{w}x{h} — works, but {RECOMMENDED_LONGEST_SIDE}px+ enables zoom"
    else:
        res_status, res_note = "pass", f"{w}x{h}"
    checks.append(Check("resolution", res_status, res_note))

    if is_main:
        if img.mode == "RGBA" and img.getchannel("A").getextrema()[0] < 255:
            checks.append(
                Check("transparency", "fail", "main image has transparency; flatten onto white")
            )
        white_ratio = _border_white_ratio(img)
        checks.append(
            Check(
                "main_white_background",
                "pass" if white_ratio >= WHITE_BORDER_MIN_RATIO else "fail",
                f"{white_ratio:.0%} of border is white (need >={WHITE_BORDER_MIN_RATIO:.0%}, "
                "pure white RGB 255,255,255)",
            )
        )
        fill = _fill_ratio(img)
        checks.append(
            Check(
                "main_product_fill",
                "pass" if fill >= MIN_FILL_RATIO else "warn",
                f"~{fill:.0%} of frame (target >={MIN_FILL_RATIO:.0%}; estimate from bounding box)",
            )
        )

    # Honest non-deterministic items: these need eyes on the pixels.
    review_items = [
        "no text, logos, watermarks, badges, or graphics (esp. on the main image)",
        "image accurately represents the actual product — no AI-hallucinated features, "
        "colors, parts, or accessories the buyer won't receive",
        "sharp, in focus, evenly lit, no artifacts",
    ]
    if is_main:
        review_items.append("main image shows ONLY the product for sale (no props/scene)")
    for item in review_items:
        checks.append(Check("human_review", "review", item))

    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a listing image against Amazon policy § 6.")
    parser.add_argument("source", help="Local path or public http(s) URL of the image.")
    parser.add_argument("--main", action="store_true", help="Apply stricter MAIN-image rules (white bg, fill).")
    parser.add_argument("--aplus", action="store_true", help="Use the 2MB A+ Content size limit.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON.")
    args = parser.parse_args()

    checks = validate(args.source, is_main=args.main, aplus=args.aplus)
    failed = [c for c in checks if c.status == "fail"]
    review = [c for c in checks if c.status == "review"]

    if args.as_json:
        print(
            json.dumps(
                {
                    "source": args.source,
                    "is_main": args.main,
                    "deterministic_pass": not failed,
                    "checks": [asdict(c) for c in checks],
                },
                indent=2,
            )
        )
    else:
        glyph = {"pass": "✓", "fail": "✗", "warn": "!", "review": "?"}
        for c in checks:
            print(f"  {glyph.get(c.status, '?')} [{c.status:6}] {c.name}: {c.detail}")
        print()
        if failed:
            print(f"FAIL — {len(failed)} deterministic check(s) failed; do NOT patch this image.")
        else:
            print("PASS — deterministic checks clear.")
        if review:
            print(
                f"REVIEW — {len(review)} item(s) a human must confirm before approving "
                "(this script cannot verify them)."
            )

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
