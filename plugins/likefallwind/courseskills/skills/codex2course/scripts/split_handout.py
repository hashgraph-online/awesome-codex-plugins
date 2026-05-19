#!/usr/bin/env python3
"""Split handout.md into per-slide markdown files based on inline markers.

Marker convention in handout.md:

    <!-- slide: Slide title here -->

Each marker opens a new slide. The slide's content is everything from the
marker up to the next marker (or end of file). Slides are numbered
sequentially starting at 001 in document order. Filenames are derived
from the title via slugify.

Usage:
    python split_handout.py <handout.md> [--out <slide-units-dir>]

Default output directory is <handout-dir>/slide-units. Existing files
matching NNN-*.md in the output directory are deleted before writing,
so removing a marker from handout.md correctly removes its slide file.
Other files in the directory are left untouched.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

MARKER_RE = re.compile(r"<!--\s*slide:\s*(.+?)\s*-->", re.IGNORECASE)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\W+", "-", text)
    return text.strip("-").lower() or "slide"


def split_handout(handout_path: Path) -> list[tuple[str, str]]:
    text = handout_path.read_text(encoding="utf-8")
    parts = MARKER_RE.split(text)
    slides: list[tuple[str, str]] = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        slides.append((title, content))
    return slides


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("handout", help="Path to handout.md")
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (default: <handout-dir>/slide-units)",
    )
    args = parser.parse_args()

    handout_path = Path(args.handout)
    if not handout_path.is_file():
        sys.exit(f"Handout not found: {handout_path}")

    out_dir = Path(args.out) if args.out else handout_path.parent / "slide-units"

    slides = split_handout(handout_path)
    if not slides:
        sys.exit("No <!-- slide: ... --> markers found in handout.")

    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("[0-9][0-9][0-9]-*.md"):
        stale.unlink()

    for n, (title, content) in enumerate(slides, 1):
        slug = slugify(title)
        filename = f"{n:03d}-{slug}.md"
        body = f"# Slide {n:03d}: {title}\n\n{content}\n"
        (out_dir / filename).write_text(body, encoding="utf-8")
        print(f"{n:03d}  {title}  ->  {filename}")


if __name__ == "__main__":
    main()
