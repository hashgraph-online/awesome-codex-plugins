#!/usr/bin/env python3
"""Пометить все строки выдачи без удаления исходных результатов."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_domain(value: str | None) -> str:
    domain = clean(value).lower()
    return domain[4:] if domain.startswith("www.") else domain


def read_lines(path: str | None) -> list[str]:
    if not path:
        return []
    return [clean(line).lower() for line in Path(path).read_text(encoding="utf-8").splitlines() if clean(line) and not clean(line).startswith("#")]


def excluded(domain: str, blocked: list[str]) -> bool:
    return any(domain == item or domain.endswith("." + item) for item in blocked)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serp-results", required=True)
    parser.add_argument("--output-tsv", required=True)
    parser.add_argument("--top-domains-file")
    parser.add_argument("--top-n", type=int, default=15)
    parser.add_argument("--max-rank-per-query-region", type=int, default=15)
    parser.add_argument("--exclude-domain", action="append", default=[])
    parser.add_argument("--exclude-domains-file")
    parser.add_argument("--exclude-url-pattern", action="append", default=[])
    parser.add_argument("--exclude-url-patterns-file")
    args = parser.parse_args()
    blocked = [normalize_domain(value) for value in args.exclude_domain + read_lines(args.exclude_domains_file)]
    patterns = [value.lower() for value in args.exclude_url_pattern + read_lines(args.exclude_url_patterns_file)]
    with Path(args.serp_results).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        source_fields = list(reader.fieldnames or [])
        required = {"search_query", "search_region", "result_rank", "result_domain", "source_url"}
        if required - set(source_fields):
            raise SystemExit(f"В исходной выдаче отсутствуют поля: {sorted(required - set(source_fields))}")
        source_rows = list(reader)
    output: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    for index, source in enumerate(source_rows, 1):
        raw = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        domain = normalize_domain(source.get("result_domain"))
        url = clean(source.get("source_url"))
        try:
            rank = int(clean(source.get("result_rank")))
        except ValueError:
            rank = 10**9
        reasons: list[str] = []
        if not domain or not url:
            reasons.append("missing_domain_or_page")
        if excluded(domain, blocked):
            reasons.append("excluded_domain_rule")
        if any(pattern in url.lower() for pattern in patterns):
            reasons.append("excluded_page_rule")
        if rank > args.max_rank_per_query_region:
            reasons.append("outside_requested_rank_window")
        if not reasons and domain:
            counts[domain] += 1
        output.append({
            **source,
            "input_order": str(index),
            "normalized_domain": domain,
            "source_row_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            "source_row_json": raw,
            "candidate_status": "pending_review" if not reasons else "needs_data",
            "rule_signals": "|".join(reasons),
            "decision": "",
            "reviewer": "",
        })
    target = Path(args.output_tsv)
    target.parent.mkdir(parents=True, exist_ok=True)
    fields = source_fields + ["input_order", "normalized_domain", "source_row_sha256", "source_row_json", "candidate_status", "rule_signals", "decision", "reviewer"]
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(output)
    if args.top_domains_file:
        candidates = [domain for domain, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[: max(args.top_n, 0)]]
        Path(args.top_domains_file).write_text("\n".join(candidates) + ("\n" if candidates else ""), encoding="utf-8")
    if len(output) != len(source_rows):
        raise SystemExit("Число строк изменилось")
    print(f"source_rows={len(source_rows)} preserved_rows={len(output)} automatic_decisions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
