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
            if kind == "top_requests" and entry.get("status") in ("success", "partial") and \
                    normalize_text(entry.get("source_mask") or entry.get("mask") or "") == mask:
                found = raw_dir / Path(str(entry.get("file", ""))).name
                if found.is_file():
                    return found
    return raw_dir / f"top_requests_{slugify_mask(mask)}.json"


def render_rows(base_dir: Path, config_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for config in config_rows:
        mask = normalize_text(config["mask"])
        raw_path = resolve_raw_path(base_dir, config["raw_dir"], mask)
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        rows.append(
            {
                "section": config["section"],
                "section_title": config["section_title"],
                "order": int(config["order"]),
                "cluster": config["cluster"],
                "mask": mask,
                "wave": config["wave"],
                # Нет totalCount (например, XMLRiver без страницы history) — пусто, а не ноль спроса.
                "total_count": int(payload["totalCount"]) if payload.get("totalCount") is not None else "",
                "request_phrase": normalize_text(payload.get("requestPhrase", "")),
                "note": normalize_text(config.get("note", "")),
                "source_file": raw_path.name,
                "source_path": str(raw_path),
            }
        )
    return sorted(rows, key=lambda row: (str(row["section"]), int(row["order"]), str(row["mask"])))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render exact Wordstat demand by approved masks without summing nested queries."
    )
    parser.add_argument("--base-dir", required=True, help="Project root")
    parser.add_argument("--config", required=True, help="TSV config with mask list")
    parser.add_argument("--output-dir", required=True, help="Directory for rendered TSV/JSON files")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).expanduser().resolve()
    config_path = Path(args.config).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config_rows = read_tsv(config_path)
    rows = render_rows(base_dir, config_rows)

    fieldnames = [
        "section",
        "section_title",
        "order",
        "cluster",
        "mask",
        "wave",
        "total_count",
        "request_phrase",
        "note",
        "source_file",
        "source_path",
    ]
    write_tsv(output_dir / "wordstat-demand-all.tsv", rows, fieldnames)

    roots = [row for row in rows if row["section"] == "roots"]
    exact = [row for row in rows if row["section"] == "exact"]
    write_tsv(output_dir / "wordstat-demand-roots.tsv", roots, fieldnames)
    write_tsv(output_dir / "wordstat-demand-exact.tsv", exact, fieldnames)

    summary = {
        "config": str(config_path),
        "rows_total": len(rows),
        "roots_rows": len(roots),
        "exact_rows": len(exact),
        "rule": "Использовать только totalCount по базовой маске. Не суммировать вложенные запросы и не складывать маски между собой как единый объем рынка.",
    }
    (output_dir / "_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
