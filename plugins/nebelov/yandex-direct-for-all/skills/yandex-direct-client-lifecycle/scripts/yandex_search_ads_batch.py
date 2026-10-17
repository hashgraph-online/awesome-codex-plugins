#!/usr/bin/env python3
"""Batch-collect Yandex search ad SERP via official Yandex Search API HTML mode."""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import stat
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
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


DEFAULT_ENDPOINT = "https://searchapi.api.cloud.yandex.net/v2/web/search"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 "
    "YaBrowser/25.2.0.0 Safari/537.36"
)
AD_RESULT_HEADER = [
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
    "raw_html_path",
    "notes",
    "serp_position",
    "ad_position",
    "count_url",
]
MANIFEST_HEADER = [
    "job_id",
    "layer",
    "purpose",
    "search_query",
    "search_region",
    "region_id",
    "page",
    "status",
    "ad_count",
    "collected_at",
    "raw_json_path",
    "raw_html_path",
    "error",
    "notes",
]
TOKEN_CLEANUP_RE = re.compile(r'^[+!"]+|[+!"]+$')
SPACE_RE = re.compile(r"\s+")
META_VALUE_RE = re.compile(r"^(snippetUrl|countUrl)$")


@dataclass
class HtmlNode:
    tag: str
    attributes: dict[str, str]
    children: list[HtmlNode | str]

    def descendants(self) -> list[HtmlNode]:
        result: list[HtmlNode] = []
        for child in self.children:
            if isinstance(child, HtmlNode):
                result.append(child)
                result.extend(child.descendants())
        return result

    def text_content(self) -> str:
        return "".join(child.text_content() if isinstance(child, HtmlNode) else child for child in self.children)

    def has_class(self, name: str, *, exact_token: bool = False) -> bool:
        value = self.attributes.get("class", "")
        return name in value.split() if exact_token else name in value


class HtmlTreeBuilder(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = HtmlNode("document", {}, [])
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = HtmlNode(tag, {key: value or "" for key, value in attrs}, [])
        self.stack[-1].children.append(node)
        if tag.lower() not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].children.append(HtmlNode(tag, {key: value or "" for key, value in attrs}, []))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag.lower() == tag.lower():
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def parse_html(html_text: str) -> HtmlNode:
    parser = HtmlTreeBuilder()
    parser.feed(html_text)
    parser.close()
    return parser.root


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-zА-Яа-яЁё._-]+", "-", value.strip())
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value[:120] or "item"


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return SPACE_RE.sub(" ", value).strip()


def is_enabled(value: str | None) -> bool:
    normalized = (value or "1").strip().lower()
    return normalized not in {"0", "false", "no", "off", "disabled"}


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_auth_and_folder(credentials_file: Path) -> tuple[dict[str, str], str]:
    if not credentials_file.is_file():
        raise RuntimeError("Явно указанный файл доступа не найден")
    if stat.S_IMODE(credentials_file.stat().st_mode) & 0o077:
        raise RuntimeError("Файл доступа должен иметь права 0600")
    payload = load_json(credentials_file)
    nested = payload.get("search_api") if isinstance(payload.get("search_api"), dict) else payload
    api_key = str(nested.get("api_key") or "").strip()
    iam_token = str(nested.get("iam_token") or "").strip()
    folder_id = str(nested.get("folder_id") or "").strip()
    if not folder_id or bool(api_key) == bool(iam_token):
        raise RuntimeError("Файл доступа должен содержать folder_id и ровно один способ авторизации")
    header = {"Authorization": f"Api-Key {api_key}"} if api_key else {"Authorization": f"Bearer {iam_token}"}
    return header, folder_id


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
            layer=clean_text(raw.get("layer")) or "ad_serp",
            purpose=clean_text(raw.get("purpose")) or "competitor_ads_capture",
            search_query=search_query,
            search_region=clean_text(raw.get("search_region")) or "rf",
            region_id=clean_text(raw.get("region_id")) or "225",
            page=int(clean_text(raw.get("page")) or "0"),
            notes=clean_text(raw.get("notes")),
        )

    def file_stub(self) -> str:
        return f"{slugify(self.job_id)}__{slugify(self.search_query)}__{slugify(self.search_region)}__p{self.page}"

    def request_body(self, folder_id: str) -> dict[str, Any]:
        return {
            "query": {
                "searchType": "ru",
                "queryText": self.search_query,
                "page": str(self.page),
                "fixTypoMode": "off",
            },
            "folderId": folder_id,
            "responseFormat": "HTML",
            "region": self.region_id,
            "l10N": "ru",
            "groupSpec": {
                "groupMode": "flat",
                "groupsOnPage": "10",
                "docsInGroup": "1",
            },
            "userAgent": DEFAULT_USER_AGENT,
        }


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


def decode_raw_data(raw_data: str) -> str:
    return base64.b64decode(raw_data).decode("utf-8", errors="ignore")


def collect_vnl_objects(item: HtmlNode) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for node in item.descendants():
        raw = node.attributes.get("data-vnl")
        if raw is None:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        if isinstance(payload, dict):
            collected.append(payload)
    return collected


def extract_feedback_meta(feedback: dict[str, Any]) -> dict[str, str]:
    result = {"feature": "", "snippet_url": "", "count_url": ""}
    for field in feedback.get("customMetaFields") or []:
        if not isinstance(field, dict):
            continue
        name = str(field.get("name") or "").strip()
        if not META_VALUE_RE.match(name):
            continue
        value = str(field.get("value") or "").strip()
        if name == "snippetUrl" and value:
            result["snippet_url"] = value
        if name == "countUrl" and value:
            result["count_url"] = value
    result["feature"] = str(feedback.get("feature") or "").strip()
    return result


def extract_ad_meta(item: HtmlNode) -> dict[str, str]:
    meta = {"feature": "", "snippet_url": "", "count_url": "", "header_title": ""}
    for payload in collect_vnl_objects(item):
        header = payload.get("headerProps")
        if isinstance(header, dict):
            header_title = str(header.get("title") or "").strip()
            if header_title and not meta["header_title"]:
                meta["header_title"] = header_title
        feedback = payload.get("reportFeedback")
        if isinstance(feedback, dict):
            extracted = extract_feedback_meta(feedback)
            for key, value in extracted.items():
                if value and not meta.get(key):
                    meta[key] = value
        for nested in payload.get("items") or []:
            if not isinstance(nested, dict):
                continue
            nested_feedback = nested.get("reportFeedback")
            if not isinstance(nested_feedback, dict):
                continue
            extracted = extract_feedback_meta(nested_feedback)
            for key, value in extracted.items():
                if value and not meta.get(key):
                    meta[key] = value
    return meta


def extract_title(item: HtmlNode, fallback: str) -> str:
    parts = [" ".join(node.text_content().split()) for node in item.descendants() if node.has_class("OrganicTitle-Link")]
    title = " ".join(part for part in parts if part).strip()
    return title or fallback


def extract_snippet(item: HtmlNode) -> str:
    parts = [" ".join(node.text_content().split()) for node in item.descendants() if node.has_class("OrganicTextContentSpan")]
    snippet = " ".join(part for part in parts if part).strip()
    if snippet:
        return snippet
    return " ".join(item.text_content().split())


def extract_href(item: HtmlNode, fallback: str) -> str:
    hrefs = [node.attributes.get("href", "").strip() for node in item.descendants() if node.has_class("OrganicTitle-Link") and node.attributes.get("href", "").strip()]
    return hrefs[0] if hrefs else fallback


def extract_domain(href: str) -> str:
    if not href:
        return ""
    parsed = urlparse(href)
    domain = parsed.netloc or parsed.path.split("/")[0]
    return domain.lower().replace("www.", "").strip()


def extract_search_ad_rows(html_text: str, job: Job, fetched_at: str, raw_json_path: Path, raw_html_path: Path) -> list[dict[str, Any]]:
    document = parse_html(html_text)
    rows: list[dict[str, Any]] = []
    ad_position = 0
    serp_position = 0
    for item in document.descendants():
        if not item.has_class("serp-item", exact_token=True):
            continue
        classes = item.attributes.get("class", "").strip()
        if "RsyaGuarantee" in classes:
            continue
        title = extract_title(item, "")
        if not title:
            continue
        serp_position += 1
        meta = extract_ad_meta(item)
        if meta["feature"] != "Реклама":
            continue
        ad_position += 1
        href = extract_href(item, meta["snippet_url"])
        snippet_url = meta["snippet_url"] or href
        domain = extract_domain(snippet_url or href)
        snippet = extract_snippet(item)
        rows.append(
            {
                "job_id": job.job_id,
                "layer": job.layer,
                "purpose": job.purpose,
                "search_query": job.search_query,
                "search_region": job.search_region,
                "region_id": job.region_id,
                "page": str(job.page),
                "group_rank": str(ad_position),
                "doc_rank": "1",
                "result_rank": str(ad_position),
                "result_title_or_snippet": clean_text(title or snippet),
                "result_title": clean_text(title),
                "result_headline": clean_text(snippet),
                "result_domain": domain,
                "source_url": snippet_url or href,
                "collected_at": fetched_at,
                "raw_json_path": str(raw_json_path),
                "raw_html_path": str(raw_html_path),
                "notes": job.notes,
                "serp_position": str(serp_position),
                "ad_position": str(ad_position),
                "count_url": meta["count_url"],
            }
        )
    return rows


def fetch_job(job: Job, output_dir: Path, endpoint: str, auth_header: dict[str, str], folder_id: str, pause_seconds: float) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    stub = job.file_stub()
    raw_json_path = output_dir / "raw_json" / f"{stub}.json"
    raw_html_path = output_dir / "raw_html" / f"{stub}.html"
    request_body = job.request_body(folder_id)
    collected_at = now_iso()
    try:
        response = requests.post(
            endpoint,
            headers={**auth_header, "Content-Type": "application/json"},
            json=request_body,
            timeout=120,
        )
        if not response.ok:
            raise RuntimeError(f"Search API error {response.status_code}: {response.text[:800]}")
        payload = response.json()
        raw_json_path.parent.mkdir(parents=True, exist_ok=True)
        raw_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raw_data = str(payload.get("rawData") or "").strip()
        if not raw_data:
            raise RuntimeError("Search API response does not contain rawData")
        html_text = decode_raw_data(raw_data)
        raw_html_path.parent.mkdir(parents=True, exist_ok=True)
        raw_html_path.write_text(html_text, encoding="utf-8")
        rows = extract_search_ad_rows(html_text, job, collected_at, raw_json_path, raw_html_path)
        manifest_row = {
            "job_id": job.job_id,
            "layer": job.layer,
            "purpose": job.purpose,
            "search_query": job.search_query,
            "search_region": job.search_region,
            "region_id": job.region_id,
            "page": str(job.page),
            "status": "ready",
            "ad_count": str(len(rows)),
            "collected_at": collected_at,
            "raw_json_path": str(raw_json_path),
            "raw_html_path": str(raw_html_path),
            "error": "",
            "notes": job.notes,
        }
        if pause_seconds > 0:
            time.sleep(pause_seconds)
        return manifest_row, rows
    except Exception as exc:  # noqa: BLE001
        manifest_row = {
            "job_id": job.job_id,
            "layer": job.layer,
            "purpose": job.purpose,
            "search_query": job.search_query,
            "search_region": job.search_region,
            "region_id": job.region_id,
            "page": str(job.page),
            "status": "failed",
            "ad_count": "0",
            "collected_at": collected_at,
            "raw_json_path": str(raw_json_path),
            "raw_html_path": str(raw_html_path),
            "error": f"{type(exc).__name__}: {exc}",
            "notes": job.notes,
        }
        return manifest_row, []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs-file", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--credentials-file", required=True, help="Закрытый файл доступа с правами 0600")
    parser.add_argument("--max-cost-units", type=int, required=True, help="Предельная стоимость волны в условных единицах")
    parser.add_argument("--cost-units-per-request", type=int, default=1)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--pause-seconds", type=float, default=0.0)
    args = parser.parse_args()

    jobs_file = Path(args.jobs_file).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    jobs = parse_jobs(jobs_file)
    if args.max_cost_units <= 0 or args.cost_units_per_request <= 0:
        parser.error("Ограничения стоимости должны быть положительными")
    planned_cost_units = len(jobs) * args.cost_units_per_request
    if planned_cost_units > args.max_cost_units:
        parser.error("Волна превышает явно заданный предел стоимости; сетевых вызовов не было")
    auth_header, folder_id = build_auth_and_folder(Path(args.credentials_file).expanduser().resolve())

    manifest_rows: list[dict[str, Any]] = []
    ad_rows: list[dict[str, Any]] = []
    for job in jobs:
        manifest_row, rows = fetch_job(job, output_dir, args.endpoint, auth_header, folder_id, args.pause_seconds)
        manifest_rows.append(manifest_row)
        ad_rows.extend(rows)

    manifest_rows.sort(key=lambda row: (row["job_id"], row["search_query"], row["search_region"]))
    ad_rows.sort(key=lambda row: (row["search_query"], row["search_region"], int(row["result_rank"]), row["result_domain"], row["source_url"]))

    write_rows(output_dir / "job_manifest.tsv", MANIFEST_HEADER, manifest_rows)
    write_rows(output_dir / "ad_rows.tsv", AD_RESULT_HEADER, ad_rows)

    summary = {
        "ok": all(row["status"] == "ready" for row in manifest_rows),
        "jobs_total": len(manifest_rows),
        "jobs_ready": sum(1 for row in manifest_rows if row["status"] == "ready"),
        "jobs_failed": sum(1 for row in manifest_rows if row["status"] != "ready"),
        "ad_rows_total": len(ad_rows),
        "unique_queries": len({row["search_query"] for row in ad_rows}),
        "unique_domains": len({row["result_domain"] for row in ad_rows if row["result_domain"]}),
        "planned_cost_units": planned_cost_units,
        "max_cost_units": args.max_cost_units,
        "credentials_source": "explicit_private_file",
    }
    (output_dir / "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if summary["jobs_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
