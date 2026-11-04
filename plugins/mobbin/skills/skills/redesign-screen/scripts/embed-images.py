#!/usr/bin/env python3
"""
Puts a filled board's images inside it, so the file opens on its own.

A board's JSON names its images by path, which only works while the images sit
beside the file. A host that sends files one at a time, or a user who forwards
the board, separates them and every pane goes blank. This swaps each image path
in #board-data for a data: URI of that file and rewrites the board in place.

  python3 embed-images.py board.html

Works on board.html, variations.html and reference-board.html. Only the fields
the templates draw as images are touched: "image", and "before" and "after" when
they hold a path, so a caption that ends in ".png" stays text. Paths resolve
from the board's own folder. A value already embedded, or a link, is left as it
is, so running it twice is safe. A path that names no file, or a file that is
not an image type below, stops the run with that path named and the board
unchanged.
"""

import base64
import json
import re
import sys
from pathlib import Path

DATA_BLOCK = re.compile(
    r'(<script type="application/json" id="board-data">)(.*?)(</script>)', re.DOTALL
)
IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".avif": "image/avif",
    ".svg": "image/svg+xml",
}
IMAGE_FIELDS = {"image", "before", "after"}


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: embed-images.py <board.html>")
    board = Path(sys.argv[1]).resolve()
    html = board.read_text(encoding="utf-8")
    block = DATA_BLOCK.search(html)
    if block is None:
        sys.exit(f"{board}: no #board-data block")

    data = json.loads(block.group(2))
    embedded, failed = [], []
    data = embed(data, board.parent, embedded, failed)
    if failed:
        sys.exit("Board left unchanged:\n  " + "\n  ".join(failed))

    # "</" is escaped so no text field can close the script tag early.
    payload = json.dumps(data, indent=2, ensure_ascii=False).replace("</", "<\\/")
    html = html[: block.start(2)] + "\n" + payload + "\n    " + html[block.end(2) :]
    board.write_text(html, encoding="utf-8")

    size = board.stat().st_size / 1024
    print(f"Embedded {len(embedded)} image(s) in {board.name} ({size:.0f} KB)")


def embed(value, folder, embedded, failed, field=None):
    """Walks the JSON and swaps each image field's local path for its data: URI."""
    if isinstance(value, dict):
        return {key: embed(item, folder, embedded, failed, key) for key, item in value.items()}
    if isinstance(value, list):
        return [embed(item, folder, embedded, failed, field) for item in value]
    if (
        not isinstance(value, str)
        or field not in IMAGE_FIELDS
        or re.match(r"^(data|https?):", value)
    ):
        return value
    media_type = IMAGE_TYPES.get(Path(value).suffix.lower())
    if media_type is None:
        failed.append(f"Not a supported image type: {value}")
        return value
    path = (folder / value).resolve()
    if not path.is_file():
        failed.append(f"Image not found: {value}")
        return value
    embedded.append(value)
    return f"data:{media_type};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


if __name__ == "__main__":
    main()
