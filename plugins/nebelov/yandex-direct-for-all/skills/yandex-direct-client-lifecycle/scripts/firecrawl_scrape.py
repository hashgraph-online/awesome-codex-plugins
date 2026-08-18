#!/usr/bin/env python3
"""Scrape public pages via Firecrawl from direct URLs or a TSV batch spec."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

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


DEFAULT_API_URL = "https://api.firecrawl.dev/v2/scrape"


def slugify_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    base = f"{host}-{path}" if path else host
    base = re.sub(r"[^a-zA-Z0-9._-]+", "-", base)
    base = re.sub(r"-{2,}", "-", base).strip("-")
    return base or "page"


def build_stem(job_id: str, url: str) -> str:
    prefix = slugify_url(job_id)
    url_slug = slugify_url(url)
    stem = f"{prefix}__{url_slug}"
    if len(stem) <= 180:
        return stem
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"{prefix[:48]}__{urlparse(url).netloc.lower()[:48]}__{digest}"


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def is_enabled(value: str | None) -> bool:
    normalized = clean_text(value or "1").lower()
    return normalized not in {"0", "false", "no", "off", "disabled"}


def parse_jobs(
    jobs_file: Path,
    url_column: str,
    id_column: str,
    notes_column: str,
) -> list[dict[str, str]]:
    with jobs_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if url_column not in (reader.fieldnames or []):
            raise ValueError(f"jobs file must include column: {url_column}")
        jobs: list[dict[str, str]] = []
        for row_number, row in enumerate(reader, start=2):
            if not is_enabled(row.get("enabled")):
                continue
            url = clean_text(row.get(url_column))
            if not url:
                raise ValueError(f"Row {row_number}: empty URL in column {url_column}")
            job_id = clean_text(row.get(id_column)) or f"capture-{row_number:03d}"
            notes = clean_text(row.get(notes_column))
            jobs.append(
                {
                    "job_id": job_id,
                    "url": url,
                    "notes": notes,
                }
            )
    return jobs


def scrape_url(
    api_key: str,
    api_url: str,
    url: str,
    formats: list[str],
    only_main_content: bool,
    proxy: str | None,
    location_country: str | None,
    location_languages: list[str],
    max_age: int | None,
) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": formats,
        "onlyMainContent": only_main_content,
    }
    if proxy:
        payload["proxy"] = proxy
    if location_country or location_languages:
        location = {}
        if location_country:
            location["country"] = location_country
        if location_languages:
            location["languages"] = location_languages
        payload["location"] = location
    if max_age is not None:
        payload["maxAge"] = max_age
    response = requests.post(api_url, headers=headers, json=payload, timeout=180)
    if not response.ok:
        raise RuntimeError(f"Firecrawl API error {response.status_code}: {response.text[:800]}")
    body = response.json()
    if body.get("success") is False:
        raise RuntimeError(f"Firecrawl scrape failed: {json.dumps(body, ensure_ascii=False)[:800]}")
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", help="Public URLs to scrape")
    parser.add_argument("--jobs-file", help="TSV batch spec with URLs to scrape")
    parser.add_argument("--output-dir", required=True, help="Directory where artifacts will be written")
    parser.add_argument(
        "--url-column",
        default="source_url",
        help="Column name containing URLs when --jobs-file is used",
    )
    parser.add_argument(
        "--id-column",
        default="capture_id",
        help="Column name used as stable file prefix when --jobs-file is used",
    )
    parser.add_argument(
        "--notes-column",
        default="notes",
        help="Column name copied into manifest notes when --jobs-file is used",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["markdown", "html"],
        help="Firecrawl formats to request (default: markdown html)",
    )
    parser.add_argument(
        "--only-main-content",
        action="store_true",
        help="Request only main content from Firecrawl",
    )
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Firecrawl scrape endpoint (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--proxy",
        choices=["basic", "enhanced", "auto"],
        default=None,
        help="Firecrawl proxy mode",
    )
    parser.add_argument(
        "--location-country",
        default=None,
        help="ISO 3166-1 alpha-2 country code for Firecrawl location emulation, e.g. RU",
    )
    parser.add_argument(
        "--location-languages",
        nargs="+",
        default=[],
        help="Preferred languages/locales for Firecrawl location, e.g. ru ru-RU",
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=None,
        help="Firecrawl maxAge in milliseconds; use 0 to force fresh fetch",
    )
    parser.add_argument(
        "--sleep-ms",
        type=int,
        default=0,
        help="Pause between jobs in milliseconds",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip jobs whose JSON artifact already exists",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Write error sidecars and continue with the next job",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit of jobs to execute",
    )
    args = parser.parse_args()

    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("FIRECRAWL_API_KEY is not set", file=sys.stderr)
        return 2

    jobs: list[dict[str, str]] = []
    if args.jobs_file:
        jobs.extend(
            parse_jobs(
                jobs_file=Path(args.jobs_file),
                url_column=args.url_column,
                id_column=args.id_column,
                notes_column=args.notes_column,
            )
        )
    jobs.extend(
        {
            "job_id": f"url-{index:03d}",
            "url": url,
            "notes": "",
        }
        for index, url in enumerate(args.urls, start=1)
    )
    if not jobs:
        print("Provide URLs or --jobs-file", file=sys.stderr)
        return 2
    if args.limit is not None:
        jobs = jobs[: args.limit]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []

    for index, job in enumerate(jobs, start=1):
        url = job["url"]
        prefix = clean_text(job.get("job_id")) or f"capture-{index:03d}"
        slug = build_stem(prefix, url)
        json_path = output_dir / f"{slug}.json"
        md_path = output_dir / f"{slug}.md"
        html_path = output_dir / f"{slug}.html"
        error_path = output_dir / f"{slug}.error.txt"
        if args.skip_existing and json_path.exists():
            manifest.append(
                {
                    "job_id": prefix,
                    "url": url,
                    "json_path": str(json_path),
                    "md_path": str(md_path) if md_path.exists() else "",
                    "html_path": str(html_path) if html_path.exists() else "",
                    "error_path": str(error_path) if error_path.exists() else "",
                    "notes": job.get("notes", ""),
                    "status": "skipped_existing",
                }
            )
            print(f"{prefix}\t{url}\t{json_path}\tskipped")
            if args.sleep_ms and index < len(jobs):
                time.sleep(args.sleep_ms / 1000)
            continue

        try:
            body = scrape_url(
                api_key=api_key,
                api_url=args.api_url,
                url=url,
                formats=args.formats,
                only_main_content=args.only_main_content,
                proxy=args.proxy,
                location_country=args.location_country,
                location_languages=args.location_languages,
                max_age=args.max_age,
            )
            json_path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")

            data = body.get("data", {})
            markdown = data.get("markdown")
            html = data.get("html") or data.get("rawHtml")

            if isinstance(markdown, str) and markdown.strip():
                write_text(md_path, markdown)
            if isinstance(html, str) and html.strip():
                write_text(html_path, html)

            manifest.append(
                {
                    "job_id": prefix,
                    "url": url,
                    "json_path": str(json_path),
                    "md_path": str(md_path) if md_path.exists() else "",
                    "html_path": str(html_path) if html_path.exists() else "",
                    "error_path": "",
                    "notes": job.get("notes", ""),
                    "status": "ok",
                }
            )
            print(f"{prefix}\t{url}\t{json_path}")
        except Exception as exc:  # noqa: BLE001
            error_path.write_text(str(exc), encoding="utf-8")
            manifest.append(
                {
                    "job_id": prefix,
                    "url": url,
                    "json_path": str(json_path),
                    "md_path": str(md_path) if md_path.exists() else "",
                    "html_path": str(html_path) if html_path.exists() else "",
                    "error_path": str(error_path),
                    "notes": job.get("notes", ""),
                    "status": "error",
                    "error": str(exc),
                }
            )
            print(f"{prefix}\t{url}\t{error_path}\terror")
            if not args.continue_on_error:
                raise
        if args.sleep_ms and index < len(jobs):
            time.sleep(args.sleep_ms / 1000)

    (output_dir / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
