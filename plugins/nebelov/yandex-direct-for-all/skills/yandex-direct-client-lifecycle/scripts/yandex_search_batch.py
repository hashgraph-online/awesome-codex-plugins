#!/usr/bin/env python3
"""Batch-collect raw Yandex Search API SERP results from a TSV job spec."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
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


DEFAULT_ENDPOINT = "https://searchapi.api.cloud.yandex.net/v2/web/search"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 "
    "YaBrowser/25.2.0.0 Safari/537.36"
)
RESULT_HEADER = [
    "job_id",
    "layer",
    "purpose",
    "search_query",
    "search_region",
    "region_id",
    "page",
    "group_rank",
    "doc_rank",
    "result_rank",
    "result_title_or_snippet",
    "result_title",
    "result_headline",
    "result_domain",
    "source_url",
    "collected_at",
    "raw_json_path",
    "raw_xml_path",
    "notes",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-zА-Яа-яЁё._-]+", "-", value.strip())
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:120] or "item"


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return clean_text("".join(element.itertext()))


def is_enabled(value: str | None) -> bool:
    normalized = (value or "1").strip().lower()
    return normalized not in {"0", "false", "no", "off", "disabled"}


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


def build_auth_header() -> dict[str, str]:
    api_key = os.environ.get("YANDEX_SEARCH_API_KEY", "").strip()
    iam_token = os.environ.get("YANDEX_SEARCH_IAM_TOKEN", "").strip()
    if api_key:
        return {"Authorization": f"Api-Key {api_key}"}
    if iam_token:
        return {"Authorization": f"Bearer {iam_token}"}
    raise RuntimeError("Set YANDEX_SEARCH_API_KEY or YANDEX_SEARCH_IAM_TOKEN")


def optional_int(value: str | None, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    return int(value)


@dataclass
class Job:
    row_number: int
    job_id: str
    layer: str
    purpose: str
    search_query: str
    search_region: str
    region_id: str
    page: int
    groups_on_page: int
    docs_in_group: int
    search_type: str
    l10n: str
    response_format: str
    group_mode: str
    family_mode: str
    fix_typo_mode: str
    sort_mode: str
    sort_order: str
    max_passages: int
    x_forwarded_for_y: str
    user_agent: str
    notes: str

    @classmethod
    def from_row(cls, row_number: int, raw: dict[str, str]) -> Job | None:
        if not is_enabled(raw.get("enabled")):
            return None
        search_query = clean_text(raw.get("search_query"))
        if not search_query:
            raise ValueError(f"Row {row_number}: search_query is required")
        job_id = clean_text(raw.get("job_id")) or f"job-{row_number:03d}"
        return cls(
            row_number=row_number,
            job_id=job_id,
            layer=clean_text(raw.get("layer")) or "organic_serp",
            purpose=clean_text(raw.get("purpose")) or "discovery",
            search_query=search_query,
            search_region=clean_text(raw.get("search_region")) or "rf",
            region_id=clean_text(raw.get("region_id")) or "225",
            page=optional_int(raw.get("page"), 0) or 0,
            groups_on_page=optional_int(raw.get("groups_on_page"), 20) or 20,
            docs_in_group=optional_int(raw.get("docs_in_group"), 1) or 1,
            search_type=clean_text(raw.get("search_type")) or "SEARCH_TYPE_RU",
            l10n=clean_text(raw.get("l10n")) or "LOCALIZATION_RU",
            response_format=clean_text(raw.get("response_format")) or "FORMAT_XML",
            group_mode=clean_text(raw.get("group_mode")) or "GROUP_MODE_FLAT",
            family_mode=clean_text(raw.get("family_mode")) or "FAMILY_MODE_MODERATE",
            fix_typo_mode=clean_text(raw.get("fix_typo_mode")) or "FIX_TYPO_MODE_ON",
            sort_mode=clean_text(raw.get("sort_mode")) or "SORT_MODE_BY_RELEVANCE",
            sort_order=clean_text(raw.get("sort_order")) or "SORT_ORDER_DESC",
            max_passages=optional_int(raw.get("max_passages"), 4) or 4,
            x_forwarded_for_y=clean_text(raw.get("x_forwarded_for_y")),
            user_agent=clean_text(raw.get("user_agent")) or DEFAULT_USER_AGENT,
            notes=clean_text(raw.get("notes")),
        )

    def file_stub(self) -> str:
        return f"{slugify(self.job_id)}__{slugify(self.search_query)}__{slugify(self.search_region)}__p{self.page}"

    def request_body(self, folder_id: str) -> dict[str, Any]:
        body: dict[str, Any] = {
            "query": {
                "searchType": self.search_type,
                "queryText": self.search_query,
                "page": self.page,
                "fixTypoMode": self.fix_typo_mode,
                "familyMode": self.family_mode,
            },
            "sortSpec": {
                "sortMode": self.sort_mode,
                "sortOrder": self.sort_order,
            },
            "groupSpec": {
                "groupMode": self.group_mode,
                "groupsOnPage": self.groups_on_page,
                "docsInGroup": self.docs_in_group,
            },
            "maxPassages": self.max_passages,
            "region": self.region_id,
            "l10N": self.l10n,
            "folderId": folder_id,
            "responseFormat": self.response_format,
            "userAgent": self.user_agent,
        }
        if self.x_forwarded_for_y:
            body["metadata"] = {"fields": {"X-Forwarded-For-Y": self.x_forwarded_for_y}}
        return body


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


def decode_raw_data(body: dict[str, Any]) -> str:
    raw = body.get("rawData")
    if not isinstance(raw, str) or not raw:
        raise RuntimeError("Search API response does not contain rawData")
    return base64.b64decode(raw).decode("utf-8", errors="replace")


def parse_xml_results(job: Job, xml_text: str, raw_json_path: Path, raw_xml_path: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    root = ET.fromstring(xml_text)
    error = root.find("./response/error")
    response_date = root.find("./response")
    collected_at = now_iso()
    if response_date is not None and response_date.attrib.get("date"):
        collected_at = response_date.attrib["date"]
    grouping = root.find("./response/results/grouping")
    found_human = clean_text(root.findtext("./response/found-human"))
    found_docs_human = ""
    rows: list[dict[str, str]] = []
    if grouping is not None:
        found_docs_human = clean_text(grouping.findtext("found-docs-human"))
        result_rank = 0
        for group_rank, group in enumerate(grouping.findall("group"), start=1):
            docs = group.findall("doc")
            for doc_rank, doc in enumerate(docs, start=1):
                result_rank += 1
                title = element_text(doc.find("title"))
                headline = element_text(doc.find("headline"))
                if not headline:
                    headline = element_text(doc.find("./passages/passage"))
                title_or_snippet = title or headline or element_text(doc.find("url"))
                rows.append(
                    {
                        "job_id": job.job_id,
                        "layer": job.layer,
                        "purpose": job.purpose,
                        "search_query": job.search_query,
                        "search_region": job.search_region,
                        "region_id": job.region_id,
                        "page": str(job.page),
                        "group_rank": str(group_rank),
                        "doc_rank": str(doc_rank),
                        "result_rank": str(result_rank),
                        "result_title_or_snippet": clean_text(title_or_snippet),
                        "result_title": title,
                        "result_headline": headline,
                        "result_domain": clean_text(doc.findtext("domain")),
                        "source_url": clean_text(doc.findtext("url")),
                        "collected_at": collected_at,
                        "raw_json_path": str(raw_json_path),
                        "raw_xml_path": str(raw_xml_path),
                        "notes": job.notes,
                    }
                )
    summary = {
        "job_id": job.job_id,
        "search_query": job.search_query,
        "search_region": job.search_region,
        "region_id": job.region_id,
        "page": job.page,
        "rows": len(rows),
        "response_error": clean_text(element_text(error)),
        "found_human": found_human,
        "found_docs_human": found_docs_human,
        "raw_json_path": str(raw_json_path),
        "raw_xml_path": str(raw_xml_path),
    }
    return rows, summary


def request_search(endpoint: str, headers: dict[str, str], body: dict[str, Any], timeout: int) -> dict[str, Any]:
    response = requests.post(endpoint, headers=headers, json=body, timeout=timeout)
    if not response.ok:
        raise RuntimeError(f"Search API error {response.status_code}: {response.text[:1200]}")
    return response.json()


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_HEADER, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs-file", required=True, help="TSV with search jobs")
    parser.add_argument("--output-dir", required=True, help="Directory for raw and normalized outputs")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help=f"Search API endpoint (default: {DEFAULT_ENDPOINT})")
    parser.add_argument("--sleep-ms", type=int, default=0, help="Pause between jobs")
    parser.add_argument("--timeout", type=int, default=180, help="HTTP timeout in seconds")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit of jobs to execute")
    parser.add_argument("--dry-run", action="store_true", help="Validate jobs and write request preview without API calls")
    args = parser.parse_args()

    jobs = parse_jobs(Path(args.jobs_file))
    if args.limit is not None:
        jobs = jobs[: args.limit]

    output_dir = Path(args.output_dir).expanduser().resolve()
    raw_json_dir = output_dir / "raw-json"
    raw_xml_dir = output_dir / "raw-xml"
    raw_json_dir.mkdir(parents=True, exist_ok=True)
    raw_xml_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, str]] = []
    manifest: list[dict[str, Any]] = []
    folder_id = os.environ.get("YANDEX_SEARCH_FOLDER_ID", "").strip() or "FOLDER_ID_REQUIRED"

    if args.dry_run:
        preview = [
            {
                "job_id": job.job_id,
                "search_query": job.search_query,
                "search_region": job.search_region,
                "request_body": job.request_body(folder_id),
            }
            for job in jobs
        ]
        (output_dir / "_requests_preview.json").write_text(
            json.dumps(preview, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "_summary.json").write_text(
            json.dumps(
                {
                    "jobs": len(jobs),
                    "rows": 0,
                    "endpoint": args.endpoint,
                    "output_dir": str(output_dir),
                    "dry_run": True,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(str(output_dir / "_requests_preview.json"))
        return 0

    folder_id = require_env("YANDEX_SEARCH_FOLDER_ID")
    headers = {
        **build_auth_header(),
        "Content-Type": "application/json",
    }

    for index, job in enumerate(jobs, start=1):
        stub = job.file_stub()
        raw_json_path = raw_json_dir / f"{stub}.json"
        raw_xml_path = raw_xml_dir / f"{stub}.xml"
        request_body = job.request_body(folder_id)
        result = request_search(args.endpoint, headers, request_body, args.timeout)
        raw_json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        xml_text = decode_raw_data(result)
        raw_xml_path.write_text(xml_text, encoding="utf-8")
        rows, summary = parse_xml_results(job, xml_text, raw_json_path, raw_xml_path)
        summary["request_index"] = index
        manifest.append(summary)
        all_rows.extend(rows)
        if args.sleep_ms and index < len(jobs):
            time.sleep(args.sleep_ms / 1000)

    write_tsv(output_dir / "serp_results.tsv", all_rows)
    (output_dir / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "_summary.json").write_text(
        json.dumps(
            {
                "jobs": len(jobs),
                "rows": len(all_rows),
                "endpoint": args.endpoint,
                "output_dir": str(output_dir),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(str(output_dir / "serp_results.tsv"))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
