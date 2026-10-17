#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    return " ".join(str(value).strip().split())


def mask_from_path(path: Path) -> str:
    name = path.stem
    if name.startswith("top_requests_"):
        return normalize_text(name.removeprefix("top_requests_"))
    return normalize_text(name)


def flatten_wave(raw_dir: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(raw_dir.glob("top_requests_*.json")):
        payload = read_json(path)
        source_mask = normalize_text(
            payload.get("requestPhrase")
            or payload.get("request")
            or payload.get("mask")
            or payload.get("query")
            or mask_from_path(path)
        )

        top_requests = payload.get("topRequests")
        if top_requests is None:
            top_requests = payload.get("results", [])

        for rank, item in enumerate(top_requests, start=1):
            rows.append(
                {
                    "source_mask": source_mask,
                    "row_type": "top_request",
                    "rank": rank,
                    "phrase": normalize_text(item.get("phrase", "")),
                    "count": int(item.get("count", 0) or 0),
                    "source_file": path.name,
                }
            )

        for rank, item in enumerate(payload.get("associations", []), start=1):
            rows.append(
                {
                    "source_mask": source_mask,
                    "row_type": "association",
                    "rank": rank,
                    "phrase": normalize_text(item.get("phrase", "")),
                    "count": int(item.get("count", 0) or 0),
                    "source_file": path.name,
                }
            )
    return rows


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = ["source_mask", "row_type", "rank", "phrase", "count", "source_file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def chunk_rows(rows: list[dict[str, object]], chunk_size: int) -> list[list[dict[str, object]]]:
    return [rows[i : i + chunk_size] for i in range(0, len(rows), chunk_size)]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Flatten, sort and chunk raw Wordstat wave files for manual review."
    )
    parser.add_argument("--raw-dir", required=True, help="Directory with top_requests_*.json")
    parser.add_argument("--output-dir", required=True, help="Where rendered TSV files will be written")
    parser.add_argument("--chunk-size", type=int, default=500, help="Rows per review chunk")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = flatten_wave(raw_dir)
    by_mask = sorted(rows, key=lambda row: (str(row["source_mask"]), str(row["row_type"]), int(row["rank"])))
    by_count = sorted(rows, key=lambda row: (-int(row["count"]), str(row["phrase"]), str(row["source_mask"])))

    write_tsv(output_dir / "all_rows_by_mask.tsv", by_mask)
    write_tsv(output_dir / "all_rows_by_count.tsv", by_count)

    chunks_dir = output_dir / "chunks_by_count"
    for idx, chunk in enumerate(chunk_rows(by_count, args.chunk_size), start=1):
        write_tsv(chunks_dir / f"chunk_{idx:03d}.tsv", chunk)

    summary = {
        "raw_dir": str(raw_dir),
        "rows_total": len(rows),
        "top_request_rows": sum(1 for row in rows if row["row_type"] == "top_request"),
        "association_rows": sum(1 for row in rows if row["row_type"] == "association"),
        "chunks_created": len(list((output_dir / "chunks_by_count").glob("chunk_*.tsv"))),
        "chunk_size": args.chunk_size,
    }
    (output_dir / "_render_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
