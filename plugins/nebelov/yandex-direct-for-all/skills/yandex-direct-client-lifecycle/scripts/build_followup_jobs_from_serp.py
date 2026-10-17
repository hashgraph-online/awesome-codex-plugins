#!/usr/bin/env python3
"""Создать выключенные задания продолжения с одной строкой на каждый источник."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def slug(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^0-9A-Za-zА-Яа-яЁё._-]+", "-", value.lower())).strip("-")[:80] or "item"


def domain_of(row: dict[str, str]) -> str:
    domain = clean(row.get("result_domain")).lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def read_list(path: str | None) -> list[str]:
    if not path:
        return []
    return [clean(line).lower() for line in Path(path).read_text(encoding="utf-8").splitlines() if clean(line) and not clean(line).startswith("#")]


def blocked(domain: str, values: list[str]) -> bool:
    return any(domain == item or domain.endswith("." + item) for item in values)


def write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serp-results", required=True)
    parser.add_argument("--page-capture-out", required=True)
    parser.add_argument("--sitemap-out", required=True)
    parser.add_argument("--exclude-domain", action="append", default=[])
    parser.add_argument("--exclude-domains-file")
    parser.add_argument("--allow-domains-file")
    parser.add_argument("--exclude-url-pattern", action="append", default=[])
    parser.add_argument("--exclude-url-patterns-file")
    parser.add_argument("--top-results-per-query-geo", type=int, default=10)
    parser.add_argument("--max-urls-per-domain", type=int, default=2)
    parser.add_argument("--max-domains", type=int)
    args = parser.parse_args()
    with Path(args.serp_results).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    excluded = [value.lower() for value in args.exclude_domain + read_list(args.exclude_domains_file)]
    allowed = set(read_list(args.allow_domains_file)) if args.allow_domains_file else None
    patterns = [value.lower() for value in args.exclude_url_pattern + read_list(args.exclude_url_patterns_file)]
    query_geo_count: defaultdict[tuple[str, str], int] = defaultdict(int)
    domain_count: defaultdict[str, int] = defaultdict(int)
    domains_seen: list[str] = []
    pages: list[dict[str, str]] = []
    sitemaps: list[dict[str, str]] = []
    for index, row in enumerate(rows, 1):
        query = clean(row.get("search_query"))
        region = clean(row.get("search_region"))
        page_url = clean(row.get("source_url"))
        domain = domain_of(row)
        raw = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        reasons: list[str] = []
        query_geo_count[(query, region)] += 1
        domain_count[domain] += 1
        if domain and domain not in domains_seen:
            domains_seen.append(domain)
        if not domain or not page_url:
            reasons.append("missing_domain_or_page")
        if blocked(domain, excluded):
            reasons.append("excluded_domain_rule")
        if allowed is not None and domain not in allowed:
            reasons.append("outside_allowed_domains")
        if any(pattern in page_url.lower() for pattern in patterns):
            reasons.append("excluded_page_rule")
        if query_geo_count[(query, region)] > args.top_results_per_query_geo:
            reasons.append("outside_query_region_window")
        if domain_count[domain] > args.max_urls_per_domain:
            reasons.append("outside_domain_url_window")
        if args.max_domains is not None and domain in domains_seen[max(args.max_domains, 0):]:
            reasons.append("outside_domain_window")
        status = "candidate" if not reasons else "skipped"
        base_url = f"{urlparse(page_url).scheme or 'https'}://{domain}" if domain else ""
        common = {
            "source_row_sha256": digest,
            "search_query": query,
            "search_region": region,
            "serp_page_url": page_url,
            "domain": domain,
            "enabled": "0",
            "status": status,
            "skip_reason": "|".join(reasons),
            "notes": "Требуется ручное включение",
        }
        pages.append({
            "capture_id": f"candidate-{index:04d}", "source_url": page_url, "brand": domain,
            "keyword": query, **common, "site_page_url": page_url, "layer": "organic_serp",
        })
        sitemaps.append({
            "site_id": f"candidate-{index:04d}-{slug(domain)}", "domain": domain, "base_url": base_url,
            "include_keywords": "", "source_row_sha256": digest, "enabled": "0", "status": status,
            "skip_reason": "|".join(reasons), "notes": "Требуется ручное включение",
        })
    page_fields = ["capture_id", "source_url", "brand", "keyword", "source_row_sha256", "search_query", "search_region", "serp_page_url", "domain", "site_page_url", "layer", "enabled", "status", "skip_reason", "notes"]
    sitemap_fields = ["site_id", "domain", "base_url", "include_keywords", "source_row_sha256", "enabled", "status", "skip_reason", "notes"]
    write(Path(args.page_capture_out), page_fields, pages)
    write(Path(args.sitemap_out), sitemap_fields, sitemaps)
    if len(pages) != len(rows) or len(sitemaps) != len(rows):
        raise SystemExit("Число строк продолжения не совпало с источником")
    print(f"source_rows={len(rows)} page_rows={len(pages)} sitemap_rows={len(sitemaps)} enabled=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
