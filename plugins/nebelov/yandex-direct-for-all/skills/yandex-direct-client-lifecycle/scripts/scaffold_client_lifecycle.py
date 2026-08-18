#!/usr/bin/env python3
"""Создать переносимый пустой проект жизненного цикла клиента."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


def load_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def render(text: str, client_key: str, client_name: str) -> str:
    return text.replace("__CLIENT_KEY__", client_key).replace("__CLIENT_NAME__", client_name)


def write_file(path: Path, content: str, force: bool) -> str:
    if path.exists() and not force:
        return f"skip\t{path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"write\t{path}"


def manifest() -> dict[str, object]:
    required = [
        "client-kb.md",
        "source-register.tsv",
        "competitor-raw-register.tsv",
        "human-review.tsv",
        "access-status.md",
        "proposal-pack.md",
        "product-map.md",
        "routing-map.tsv",
        "landing-inventory.tsv",
        "fact-check-log.tsv",
        ".codex/yandex-performance-client.json",
        "research/analysis/company-footprint.md",
        "research/analysis/landing-inventory.md",
        "research/analysis/research-backlog.md",
        "research/jobs/organic-serp-jobs.tsv",
        "research/jobs/ad-serp-jobs.tsv",
        "research/jobs/page-capture-jobs.tsv",
        "research/jobs/sitemap-jobs.tsv",
    ]
    return {
        "schema_version": "1.0",
        "artifacts": [{"path": path, "kind": "file", "required": True} for path in required],
        "tsv_contracts": {
            "source-register.tsv": [
                "source_id", "source_type", "source_url", "captured_at", "status",
                "evidence_path", "reviewer", "reviewed_at", "expires_at", "reversal_ref",
            ],
            "routing-map.tsv": [
                "intent", "domain", "serp_page_url", "site_page_url", "campaign_name", "adgroup_name",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--client-key", required=True)
    parser.add_argument("--client-name", required=True)
    parser.add_argument("--force", action="store_true", help="Явно заменить существующие файлы")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{1,63}", args.client_key):
        parser.error("client-key должен быть переносимым коротким ключом")
    if not args.client_name.strip():
        parser.error("client-name не может быть пустым")

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "client-kb.md": render(load_template("client-kb-template.md"), args.client_key, args.client_name),
        "source-register.tsv": load_template("source-register-template.tsv"),
        "competitor-raw-register.tsv": load_template("competitor-raw-register-template.tsv"),
        "human-review.tsv": load_template("human-review-template.tsv"),
        "access-status.md": load_template("access-status-template.md"),
        "proposal-pack.md": render(load_template("proposal-pack-template.md"), args.client_key, args.client_name),
        "product-map.md": load_template("product-map-template.md"),
        "routing-map.tsv": load_template("routing-map-template.tsv"),
        "landing-inventory.tsv": load_template("landing-inventory-tsv-template.tsv"),
        "fact-check-log.tsv": load_template("fact-check-log-template.tsv"),
        "research/analysis/company-footprint.md": render(load_template("company-footprint-template.md"), args.client_key, args.client_name),
        "research/analysis/landing-inventory.md": load_template("landing-inventory-template.md"),
        "research/analysis/research-backlog.md": load_template("research-backlog-template.md"),
        "research/analysis/единая-карта-конкурентов.md": load_template("unified-competitor-map-template.md").replace("__DATE__", "YYYY-MM-DD"),
        "research/analysis/пакет-структуры-будущего-кабинета.md": load_template("future-cabinet-structure-template.md").replace("__DATE__", "YYYY-MM-DD"),
        "research/analysis/пакет-текстов-и-офферов.md": load_template("offers-pack-template.md").replace("__DATE__", "YYYY-MM-DD"),
        "research/analysis/готовые-тексты-для-директа.tsv": load_template("direct-copy-pack-template.tsv"),
        f"research/semantics/{args.client_key}/00-product-map.md": load_template("semantics-product-map-template.md"),
        f"research/semantics/{args.client_key}/01-masks-wave1.tsv": load_template("wordstat-masks-wave1-template.tsv"),
        "research/jobs/organic-serp-jobs.tsv": load_template("serp-job-template.tsv"),
        "research/jobs/ad-serp-jobs.tsv": load_template("ad-serp-job-template.tsv"),
        "research/jobs/page-capture-jobs.tsv": load_template("page-capture-job-template.tsv"),
        "research/jobs/sitemap-jobs.tsv": load_template("sitemap-job-template.tsv"),
        "research/jobs/search-api.env.example": load_template("search-api-env-template.env"),
        ".codex/yandex-performance-client.json": render(load_template("yandex-performance-client-template.json"), args.client_key, args.client_name),
        "research-manifest.json": json.dumps(manifest(), ensure_ascii=False, indent=2) + "\n",
    }
    results = [write_file(output_dir / relative, content, args.force) for relative, content in files.items()]
    for relative in ["research/raw", "proposal", "handoff"]:
        (output_dir / relative).mkdir(parents=True, exist_ok=True)
    print("\n".join(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
