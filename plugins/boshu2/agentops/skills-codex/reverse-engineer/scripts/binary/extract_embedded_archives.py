#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path


@dataclass(frozen=True)
class Candidate:
    offset: int
    file_count: int
    score: int


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_offsets(data: bytes, max_hits: int = 5000) -> list[int]:
    sig = b"PK\x03\x04"
    hits: list[int] = []
    start = 0
    while len(hits) < max_hits:
        i = data.find(sig, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    return hits


def _score_names(names: list[str]) -> int:
    exts = {".py": 5, ".js": 4, ".ts": 4, ".go": 4, ".md": 2, ".yaml": 2, ".yml": 2, ".json": 2, ".toml": 2}
    score = 0
    for n in names:
        for ext, w in exts.items():
            if n.endswith(ext):
                score += w
                break
    # Reward file count lightly.
    score += min(len(names), 200)
    return score


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--out-dir", required=True, help="Directory to extract archives into.")
    ap.add_argument("--max-candidates", type=int, default=200)
    args = ap.parse_args()

    binary = Path(args.binary)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    data = binary.read_bytes()
    offsets = _find_offsets(data)

    cands: list[Candidate] = []
    opened = 0
    for off in offsets[: args.max_candidates]:
        try:
            with zipfile.ZipFile(BytesIO(data[off:])) as zf:
                names = zf.namelist()
                cands.append(Candidate(offset=off, file_count=len(names), score=_score_names(names)))
                opened += 1
        except Exception:
            continue

    if not cands:
        (out_dir / "extract.NOOP.md").write_text(
            f"# Extract Embedded Archives (No-Op)\n\nNo embedded ZIP archives could be opened.\n\nBinary: `{binary}`\n",
            encoding="utf-8",
        )
        return 0

    best = sorted(cands, key=lambda c: (-c.score, -c.file_count, c.offset))[0]
    dest = out_dir / f"zip@{best.offset}"
    dest.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(BytesIO(data[best.offset:])) as zf:
        # Extract all files. This is an authorized-only operation; do not commit the result.
        zf.extractall(dest)
        names = zf.namelist()

    manifest = {
        "binary": str(binary),
        "binary_sha256": _sha256_file(binary),
        "selected_offset": best.offset,
        "selected_file_count": best.file_count,
        "selected_score": best.score,
        "filenames": names[:500],
        "note": "Do not paste or commit extracted content. Reports must reference paths/hashes only.",
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Convenience pointer for downstream scripts.
    (out_dir / "PRIMARY.txt").write_text(str(dest), encoding="utf-8")

    print(f"OK: extracted {best.file_count} files to {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

