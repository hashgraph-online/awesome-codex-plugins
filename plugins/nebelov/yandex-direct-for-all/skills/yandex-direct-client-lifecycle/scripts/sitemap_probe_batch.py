#!/usr/bin/env python3
"""Batch-discover sitemap and candidate URLs for public sites."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

for candidate in (
    Path(__file__).resolve().parents[3] / "scripts",
    Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "plugins/yandex-direct-for-all/scripts",
    Path(os.environ.get("CLAUDE_HOME", Path.home() / ".claude")) / "plugins/yandex-direct-for-all/scripts",
):
    if (candidate / "portable_http.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise RuntimeError("Не найден переносимый HTTP-слой yandex-direct-for-all")

import portable_http as requests  # noqa: E402


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
)
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-zА-Яа-яЁё._-]+", "-", value.strip())
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:120] or "item"


def is_enabled(value: str | None) -> bool:
    normalized = clean_text(value or "1").lower()
    return normalized not in {"0", "false", "no", "off", "disabled"}


def as_list(value: str | None) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    return [item for item in re.split(r"[,\n;|]+", text) if item.strip()]


def read_patterns(path: Path) -> list[str]:
    patterns: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = clean_text(line)
        if not value or value.startswith("#"):
            continue
        patterns.append(value.lower())
    return patterns


@dataclass
class Job:
    site_id: str
    base_url: str
    include_keywords: list[str]
    notes: str

    @classmethod
    def from_row(cls, row_number: int, row: dict[str, str]) -> "Job | None":
        if not is_enabled(row.get("enabled")):
            return None
        base_url = clean_text(row.get("base_url"))
        if not base_url:
            raise ValueError(f"Row {row_number}: base_url is required")
        if not base_url.startswith(("http://", "https://")):
            base_url = "https://" + base_url
        site_id = clean_text(row.get("site_id")) or f"site-{row_number:03d}"
        return cls(
            site_id=site_id,
            base_url=base_url.rstrip("/"),
            include_keywords=[item.lower() for item in as_list(row.get("include_keywords"))],
            notes=clean_text(row.get("notes")),
        )


def parse_jobs(path: Path) -> list[Job]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if "base_url" not in (reader.fieldnames or []):
            raise ValueError("jobs file must include column: base_url")
        jobs: list[Job] = []
        for row_number, row in enumerate(reader, start=2):
            job = Job.from_row(row_number, row)
            if job:
                jobs.append(job)
    return jobs


def fetch_text(session: requests.Session, url: str, timeout: int) -> tuple[int, str]:
    response = session.get(url, timeout=timeout, allow_redirects=True)
    return response.status_code, response.text


def sitemap_candidates(base_url: str, robots_text: str) -> list[str]:
    found = []
    for line in robots_text.splitlines():
        if line.lower().startswith("sitemap:"):
            value = line.split(":", 1)[1].strip()
            if value:
                found.append(value)
    defaults = [
        urljoin(base_url + "/", "sitemap.xml"),
        urljoin(base_url + "/", "sitemap_index.xml"),
        urljoin(base_url + "/", "sitemap-index.xml"),
    ]
    ordered = []
    seen = set()
    for item in found + defaults:
        key = item.strip()
        if key and key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def parse_sitemap(xml_text: str) -> tuple[list[str], list[str]]:
    root = ET.fromstring(xml_text)
    tag = root.tag.lower()
    child_sitemaps: list[str] = []
    urls: list[str] = []
    if tag.endswith("sitemapindex"):
        for loc in root.findall(".//sm:sitemap/sm:loc", NS):
            value = clean_text(loc.text)
            if value:
                child_sitemaps.append(value)
    elif tag.endswith("urlset"):
        for loc in root.findall(".//sm:url/sm:loc", NS):
            value = clean_text(loc.text)
            if value:
                urls.append(value)
    return child_sitemaps, urls


def keyword_match(url: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    text = url.lower()
    return any(keyword in text for keyword in keywords)


def candidate_allowed(url: str, keywords: list[str], excluded_patterns: list[str]) -> bool:
    text = url.lower()
    if excluded_patterns and any(pattern in text for pattern in excluded_patterns):
        return False
    return keyword_match(url, keywords)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs-file", required=True, help="TSV with sitemap probe jobs")
    parser.add_argument("--output-dir", required=True, help="Directory for raw sitemap artifacts")
    parser.add_argument("--sleep-ms", type=int, default=0, help="Pause between jobs")
    parser.add_argument("--timeout", type=int, default=45, help="HTTP timeout in seconds")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit of jobs to execute")
    parser.add_argument("--max-sitemaps", type=int, default=20, help="Max sitemap files per site")
    parser.add_argument("--max-relevant-urls-per-site", type=int, default=None, help="Optional cap for matched candidate URLs per site")
    parser.add_argument("--exclude-candidate-pattern", action="append", default=[], help="Substring pattern to exclude candidate URLs")
    parser.add_argument("--exclude-candidate-patterns-file", help="File with candidate URL exclude substrings")
    args = parser.parse_args()

    jobs = parse_jobs(Path(args.jobs_file))
    if args.limit is not None:
        jobs = jobs[: args.limit]

    output_dir = Path(args.output_dir).expanduser().resolve()
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, str]] = []
    candidate_rows: list[dict[str, str]] = []
    excluded_candidate_patterns = [item.lower() for item in args.exclude_candidate_pattern]
    if args.exclude_candidate_patterns_file:
        excluded_candidate_patterns.extend(read_patterns(Path(args.exclude_candidate_patterns_file).expanduser().resolve()))

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    for index, job in enumerate(jobs, start=1):
        site_stub = slugify(job.site_id)
        site_dir = raw_dir / site_stub
        site_dir.mkdir(parents=True, exist_ok=True)

        robots_url = urljoin(job.base_url + "/", "robots.txt")
        robots_status = ""
        robots_text = ""
        try:
            status_code, robots_text = fetch_text(session, robots_url, args.timeout)
            robots_status = str(status_code)
            (site_dir / "robots.txt").write_text(robots_text, encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            robots_status = f"error:{exc}"
            (site_dir / "robots_error.txt").write_text(str(exc), encoding="utf-8")

        queue = sitemap_candidates(job.base_url, robots_text)
        seen_sitemaps = set()
        processed = 0
        site_candidate_count = 0

        while queue and processed < args.max_sitemaps:
            sitemap_url = queue.pop(0)
            if sitemap_url in seen_sitemaps:
                continue
            seen_sitemaps.add(sitemap_url)
            processed += 1

            parsed = urlparse(sitemap_url)
            file_stub = slugify(parsed.netloc + parsed.path)
            status = ""
            child_count = 0
            url_count = 0
            relevant_count = 0

            try:
                status_code, xml_text = fetch_text(session, sitemap_url, args.timeout)
                status = str(status_code)
                (site_dir / f"{file_stub}.xml").write_text(xml_text, encoding="utf-8")
                if status_code == 200:
                    child_sitemaps, urls = parse_sitemap(xml_text)
                    child_count = len(child_sitemaps)
                    url_count = len(urls)
                    for child in child_sitemaps:
                        if child not in seen_sitemaps:
                            queue.append(child)
                    for found_url in urls:
                        if args.max_relevant_urls_per_site is not None and site_candidate_count >= args.max_relevant_urls_per_site:
                            break
                        if candidate_allowed(found_url, job.include_keywords, excluded_candidate_patterns):
                            relevant_count += 1
                            site_candidate_count += 1
                            candidate_rows.append(
                                {
                                    "site_id": job.site_id,
                                    "base_url": job.base_url,
                                    "candidate_url": found_url,
                                    "matched_keywords": ",".join(
                                        [keyword for keyword in job.include_keywords if keyword in found_url.lower()]
                                    ),
                                    "source_sitemap": sitemap_url,
                                    "notes": job.notes,
                                }
                            )
            except Exception as exc:  # noqa: BLE001
                status = f"error:{exc}"
                (site_dir / f"{file_stub}.error.txt").write_text(str(exc), encoding="utf-8")

            manifest_rows.append(
                {
                    "site_id": job.site_id,
                    "base_url": job.base_url,
                    "robots_url": robots_url,
                    "robots_status": robots_status,
                    "sitemap_url": sitemap_url,
                    "status": status,
                    "child_sitemaps": str(child_count),
                    "urls_found": str(url_count),
                    "relevant_urls": str(relevant_count),
                    "notes": job.notes,
                }
            )

        if args.sleep_ms and index < len(jobs):
            time.sleep(args.sleep_ms / 1000)

    with (output_dir / "sitemap_manifest.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "site_id",
                "base_url",
                "robots_url",
                "robots_status",
                "sitemap_url",
                "status",
                "child_sitemaps",
                "urls_found",
                "relevant_urls",
                "notes",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    with (output_dir / "candidate_urls.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "site_id",
                "base_url",
                "candidate_url",
                "matched_keywords",
                "source_sitemap",
                "notes",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(candidate_rows)

    (output_dir / "_summary.json").write_text(
        json.dumps(
            {
                "jobs": len(jobs),
                "sitemaps_processed": len(manifest_rows),
                "candidate_urls": len(candidate_rows),
                "output_dir": str(output_dir),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(str(output_dir / "candidate_urls.tsv"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
