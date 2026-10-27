#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def normalize_text(value: str) -> str:
    return " ".join(str(value).strip().split())


def slugify_mask(mask: str) -> str:
    return normalize_text(mask).replace(" ", "_")


def resolve_raw_path(base_dir: Path, raw_dir_value: str, mask: str) -> Path:
    raw_dir = Path(raw_dir_value)
    if not raw_dir.is_absolute():
        raw_dir = (base_dir / raw_dir).resolve()
    manifest = raw_dir / "_manifest.json"
    if manifest.is_file():
        # Сборщики (Yandex Cloud и XMLRiver) пишут имя с хешем маски; путь берётся из их манифеста.
        for entry in json.loads(manifest.read_text(encoding="utf-8")):
            kind = str(entry.get("artifact") or entry.get("type") or "")
            if kind == "dynamics" and entry.get("status") in ("success", "partial") and \
                    normalize_text(entry.get("source_mask") or entry.get("mask") or "") == mask:
                found = raw_dir / Path(str(entry.get("file", ""))).name
                if found.is_file():
                    return found
    return raw_dir / f"dynamics_{slugify_mask(mask)}.json"


def render_rows(base_dir: Path, config_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[str]]:
    rows: list[dict[str, object]] = []
    all_dates: set[str] = set()
    for config in config_rows:
        mask = normalize_text(config["mask"])
        raw_path = resolve_raw_path(base_dir, config["raw_dir"], mask)
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        points = payload.get("dynamics", [])
        for point in points:
            date = str(point.get("date", ""))
            all_dates.add(date)
            rows.append(
                {
                    "section": config.get("section", "exact"),
                    "section_title": config.get("section_title", "Точные базовые маски"),
                    "order": int(config["order"]),
                    "cluster": config["cluster"],
                    "mask": mask,
                    "request_phrase": normalize_text(payload.get("requestPhrase", "")),
                    "date": date,
                    "count": int(point.get("count", 0) or 0),
                    "share": point.get("share", ""),
                    "note": normalize_text(config.get("note", "")),
                    "source_file": raw_path.name,
                    "source_path": str(raw_path),
                }
            )
    return sorted(rows, key=lambda row: (int(row["order"]), str(row["mask"]), str(row["date"]))), sorted(all_dates)


def build_matrix(rows: list[dict[str, object]], dates: list[str]) -> list[dict[str, object]]:
    matrix: dict[str, dict[str, object]] = {}
    for row in rows:
        key = str(row["mask"])
        record = matrix.setdefault(
            key,
            {
                "order": int(row["order"]),
                "cluster": row["cluster"],
                "mask": row["mask"],
                "note": row["note"],
            },
        )
        record[str(row["date"])] = int(row["count"])
    return sorted(matrix.values(), key=lambda row: (int(row["order"]), str(row["mask"])))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render Wordstat seasonality by approved masks from collected dynamics JSON files."
    )
    parser.add_argument("--base-dir", required=True, help="Project root")
    parser.add_argument("--config", required=True, help="TSV config with seasonality masks")
    parser.add_argument("--output-dir", required=True, help="Directory for rendered TSV/JSON files")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config_rows = read_tsv(config_path)
    rows, dates = render_rows(base_dir, config_rows)

    all_fieldnames = [
        "section",
        "section_title",
        "order",
        "cluster",
        "mask",
        "request_phrase",
        "date",
        "count",
        "share",
        "note",
        "source_file",
        "source_path",
    ]
    write_tsv(output_dir / "wordstat-seasonality-all.tsv", rows, all_fieldnames)

    matrix_rows = build_matrix(rows, dates)
    matrix_fieldnames = ["order", "cluster", "mask", *dates, "note"]
    write_tsv(output_dir / "wordstat-seasonality-matrix.tsv", matrix_rows, matrix_fieldnames)

    summary = {
        "config": str(config_path),
        "rows_total": len(rows),
        "mask_rows": len(matrix_rows),
        "dates": dates,
        "rule": "Скрипт только рендерит помесячные точки из собранного raw и не делает выводов.",
    }
    (output_dir / "_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
