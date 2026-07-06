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
class ZipCandidate:
    offset: int
    file_count: int
    names: list[str]
    sha256: str


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _find_zip_offsets(data: bytes, max_hits: int = 5000) -> list[int]:
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


def _try_open_zip(data: bytes, offset: int) -> ZipCandidate | None:
    tail = data[offset:]
    # zipfile wants central directory present; if it's not, this will fail (that's fine).
    bio = BytesIO(tail)
    try:
        with zipfile.ZipFile(bio) as zf:
            names = zf.namelist()
            # Hash just the first ~4MB for stable fingerprint without storing full content.
            sha = _sha256_bytes(tail[: 4 * 1024 * 1024])
            return ZipCandidate(offset=offset, file_count=len(names), names=names[:200], sha256=sha)
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-index-md", required=True)
    args = ap.parse_args()

    binary = Path(args.binary)
    data = binary.read_bytes()

    hits = _find_zip_offsets(data)
    cands: list[ZipCandidate] = []
    # Try a limited number to keep runtime bounded.
    for off in hits[:200]:
        cand = _try_open_zip(data, off)
        if cand:
            cands.append(cand)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            {
                "binary": str(binary),
                "zip_header_hits": len(hits),
                "candidates": [
                    {"offset": c.offset, "file_count": c.file_count, "sha256_head_4mb": c.sha256, "names": c.names}
                    for c in sorted(cands, key=lambda x: (-x.file_count, x.offset))
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    out_md = Path(args.out_index_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Embedded Archive Index (Best-Effort)")
    lines.append("")
    lines.append("Guardrail: this index does not dump reconstructed source or prompts; it only inventories candidate archives.")
    lines.append("")
    lines.append(f"- Binary: `{binary}`")
    lines.append(f"- ZIP header hits: {len(hits)}")
    lines.append(f"- ZIP candidates opened: {len(cands)}")
    lines.append("")
    if not cands:
        lines.append("_No embedded ZIP archives could be opened via the central directory heuristic._")
        lines.append("")
    else:
        for i, c in enumerate(sorted(cands, key=lambda x: (-x.file_count, x.offset))[:5], start=1):
            lines.append(f"## Candidate {i}")
            lines.append("")
            lines.append(f"- Offset: `{c.offset}`")
            lines.append(f"- File count: `{c.file_count}`")
            lines.append(f"- SHA256(head_4mb): `{c.sha256}`")
            lines.append("")
            lines.append("Top filenames (truncated):")
            lines.append("")
            for n in c.names[:30]:
                lines.append(f"- `{n}`")
            lines.append("")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

