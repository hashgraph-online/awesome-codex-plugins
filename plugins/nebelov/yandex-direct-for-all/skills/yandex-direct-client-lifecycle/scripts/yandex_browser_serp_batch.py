#!/usr/bin/env python3
"""Сохранить необязательные диагностические снимки браузерной выдачи."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


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


@dataclass
class Job:
    job_id: str
    layer: str
    purpose: str
    search_query: str
    search_region: str
    region_id: str
    notes: str

    @classmethod
    def from_row(cls, row_number: int, row: dict[str, str]) -> Job | None:
        if not is_enabled(row.get("enabled")):
            return None
        query = clean_text(row.get("search_query"))
        if not query:
            raise ValueError(f"Row {row_number}: search_query is required")
        return cls(
            job_id=clean_text(row.get("job_id")) or f"job-{row_number:03d}",
            layer=clean_text(row.get("layer")) or "serp_snapshot",
            purpose=clean_text(row.get("purpose")) or "ad_serp_capture",
            search_query=query,
            search_region=clean_text(row.get("search_region")) or "rf",
            region_id=clean_text(row.get("region_id")) or "225",
            notes=clean_text(row.get("notes")),
        )

    def stub(self) -> str:
        return f"{slugify(self.job_id)}__{slugify(self.search_query)}__{slugify(self.search_region)}"

    def url(self, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/search/?text={quote_plus(self.search_query)}&lr={self.region_id}"


def parse_jobs(path: Path) -> list[Job]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if "search_query" not in (reader.fieldnames or []):
            raise ValueError("jobs file must include column: search_query")
        jobs: list[Job] = []
        for row_number, row in enumerate(reader, start=2):
            job = Job.from_row(row_number, row)
            if job:
                jobs.append(job)
    return jobs


def try_accept_banners(page) -> None:
    selectors = [
        "button:has-text('Принять')",
        "button:has-text('Согласен')",
        "button:has-text('Понятно')",
        "button:has-text('Accept')",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=1000):
                locator.click(timeout=1000)
                return
        except Exception:  # noqa: BLE001
            continue


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs-file", required=True, help="TSV batch spec with search jobs")
    parser.add_argument("--output-dir", required=True, help="Directory for screenshots/html/json")
    parser.add_argument("--base-url", default="https://yandex.ru", help="Yandex base URL")
    parser.add_argument("--sleep-ms", type=int, default=1500, help="Pause between jobs")
    parser.add_argument("--timeout-ms", type=int, default=45000, help="Page timeout in milliseconds")
    parser.add_argument("--wait-ms", type=int, default=4000, help="Post-load wait before capture")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit of jobs to execute")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    args = parser.parse_args()

    jobs = parse_jobs(Path(args.jobs_file))
    if args.limit is not None:
        jobs = jobs[: args.limit]

    output_dir = Path(args.output_dir).expanduser().resolve()
    html_dir = output_dir / "html"
    png_dir = output_dir / "screenshots"
    meta_dir = output_dir / "meta"
    html_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, str]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            locale="ru-RU",
            viewport={"width": 1440, "height": 2200},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 "
                "YaBrowser/25.2.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.set_default_timeout(args.timeout_ms)

        for index, job in enumerate(jobs, start=1):
            target_url = job.url(args.base_url)
            stub = job.stub()
            html_path = html_dir / f"{stub}.html"
            png_path = png_dir / f"{stub}.png"
            meta_path = meta_dir / f"{stub}.json"
            error = ""
            captcha_signal = False
            try:
                page.goto(target_url, wait_until="domcontentloaded")
                page.wait_for_timeout(args.wait_ms)
                try_accept_banners(page)
                page.wait_for_timeout(800)
                html_path.write_text(page.content(), encoding="utf-8")
                page.screenshot(path=str(png_path), full_page=True)
                meta = {
                    "job_id": job.job_id,
                    "layer": job.layer,
                    "purpose": job.purpose,
                    "search_query": job.search_query,
                    "search_region": job.search_region,
                    "region_id": job.region_id,
                    "requested_url": target_url,
                    "final_url": page.url,
                    "title": page.title(),
                    "captcha_signal": "captcha" in page.url.lower() or "робот" in page.content().lower(),
                    "diagnostic_only": True,
                    "notes": job.notes,
                }
                captcha_signal = bool(meta["captcha_signal"])
            except PlaywrightTimeoutError as exc:
                error = f"timeout: {exc}"
                meta = {
                    "job_id": job.job_id,
                    "requested_url": target_url,
                    "final_url": page.url,
                    "error": error,
                    "captcha_signal": False,
                    "diagnostic_only": True,
                    "notes": job.notes,
                }
                html_path.write_text(page.content(), encoding="utf-8")
                page.screenshot(path=str(png_path), full_page=True)
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
                meta = {
                    "job_id": job.job_id,
                    "requested_url": target_url,
                    "final_url": page.url,
                    "error": error,
                    "captcha_signal": False,
                    "diagnostic_only": True,
                    "notes": job.notes,
                }
                html_path.write_text(page.content(), encoding="utf-8")
                page.screenshot(path=str(png_path), full_page=True)

            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            manifest.append(
                {
                    "job_id": job.job_id,
                    "search_query": job.search_query,
                    "search_region": job.search_region,
                    "requested_url": target_url,
                    "html_path": str(html_path),
                    "png_path": str(png_path),
                    "meta_path": str(meta_path),
                    "error": error,
                    "captcha_signal": captcha_signal,
                    "status": "incomplete" if error or captcha_signal else "captured",
                    "diagnostic_only": True,
                }
            )
            print(f"{job.job_id}\t{target_url}\t{png_path}")
            if args.sleep_ms and index < len(jobs):
                time.sleep(args.sleep_ms / 1000)

        context.close()
        browser.close()

    summary = {
        "diagnostic_only": True,
        "source_of_truth": False,
        "jobs_total": len(manifest),
        "captured": sum(1 for item in manifest if item["status"] == "captured"),
        "incomplete": sum(1 for item in manifest if item["status"] != "captured"),
        "captcha_signals": sum(1 for item in manifest if item["captcha_signal"]),
        "rows": manifest,
    }
    (output_dir / "_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
