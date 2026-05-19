#!/usr/bin/env python3
"""Combine slide images from a directory into a single PDF file.

Images are sorted by filename (ascending), so the naming convention
000-cover.png < 001-*.png < ... < zzz-ending.png produces the correct
page order automatically.

Usage:
    python images2pdf.py <slides-dir> [output.pdf]

If output is omitted, the script reads <slides-dir>/../outline.md and
uses its H1 (e.g. `# 课程标题: Vibe Coding 101` -> `Vibe Coding 101.pdf`)
as the filename. Falls back to `course-deck.pdf` if outline.md or its
H1 is missing.

Supported image formats: PNG, JPG/JPEG, WEBP, BMP, TIFF.
"""
import argparse
import re
import sys
from pathlib import Path

SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

# Characters that are illegal or troublesome across Linux/macOS/Windows filesystems.
_FILENAME_BAD = re.compile(r'[\\/:*?"<>|\r\n\t]+')
# Common H1 prefixes to strip when the title line is something like "课程标题: X" or "Course: X".
_TITLE_PREFIX = re.compile(r"^(?:课程标题|课程名称|课程|标题|title|course)\s*[:：]\s*", re.IGNORECASE)


def collect_images(slides_dir: Path) -> list[Path]:
    paths = sorted(
        p for p in slides_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )
    return paths


def extract_course_title(outline_path: Path) -> str | None:
    if not outline_path.is_file():
        return None
    for line in outline_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            title = _TITLE_PREFIX.sub("", title).strip()
            return title or None
    return None


def sanitize_filename(name: str) -> str:
    cleaned = _FILENAME_BAD.sub(" ", name).strip().rstrip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def default_output_path(slides_dir: Path) -> Path:
    parent = slides_dir.parent
    title = extract_course_title(parent / "outline.md")
    if title:
        safe = sanitize_filename(title)
        if safe:
            return parent / f"{safe}.pdf"
    return parent / "course-deck.pdf"


def build_pdf(image_paths: list[Path], output: Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is required: pip install Pillow")

    imgs = [Image.open(p).convert("RGB") for p in image_paths]
    output.parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(output, save_all=True, append_images=imgs[1:])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("slides_dir", help="Directory containing slide images")
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output PDF path (default: <slides-dir>/../<course title>.pdf, "
             "derived from outline.md's H1; falls back to course-deck.pdf)",
    )
    args = parser.parse_args()

    slides_dir = Path(args.slides_dir)
    if not slides_dir.is_dir():
        sys.exit(f"Slides directory not found: {slides_dir}")

    output = Path(args.output) if args.output else default_output_path(slides_dir)

    image_paths = collect_images(slides_dir)
    if not image_paths:
        sys.exit(f"No supported images found in: {slides_dir}")

    print(f"Found {len(image_paths)} images:")
    for p in image_paths:
        print(f"  {p.name}")

    build_pdf(image_paths, output)
    print(f"\nPDF saved to: {output}")


if __name__ == "__main__":
    main()
