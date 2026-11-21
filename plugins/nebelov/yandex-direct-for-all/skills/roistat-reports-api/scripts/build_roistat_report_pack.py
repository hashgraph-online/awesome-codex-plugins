#!/usr/bin/env python3
"""Собрать воспроизводимый пакет чтения Roistat с раздельными источниками."""

from __future__ import annotations

import argparse
import csv
import json
import os
import stat
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


DEFAULT_METRICS = ["marketing_cost", "visits", "leads", "sales", "revenue"]
Fetcher = Callable[[str, dict[str, Any]], dict[str, Any]]


def private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)


def atomic_json(path: Path, value: Any) -> None:
    private_dir(path.parent)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    private_dir(path.parent)
    fields = sorted({key for row in rows for key in row})
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            if fields:
                writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_access(path: Path | None) -> tuple[str, str, str]:
    value: dict[str, Any] = {}
    if path:
        if not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise RuntimeError("Файл доступа Roistat должен существовать и иметь права 0600")
        value = json.loads(path.read_text(encoding="utf-8"))
    project = os.environ.get("ROISTAT_PROJECT", "").strip() or str(value.get("project") or "").strip()
    api_key = os.environ.get("ROISTAT_API_KEY", "").strip() or str(value.get("api_key") or "").strip()
    base_url = os.environ.get("ROISTAT_BASE_URL", "").strip() or str(value.get("base_url") or "https://cloud.roistat.com/api/v1").strip()
    if not project or not api_key:
        raise RuntimeError("Нужны ROISTAT_PROJECT и ROISTAT_API_KEY либо закрытый файл доступа")
    return project, api_key, base_url


def api_call(base_url: str, project: str, api_key: str, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/{endpoint}?project={urllib.parse.quote(project)}"
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{endpoint}: HTTP {exc.code}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{endpoint}: ответ не является JSON") from exc
    if not isinstance(value, dict) or value.get("status") == "error":
        raise RuntimeError(f"{endpoint}: интерфейс вернул ошибку")
    return value


def paginate(fetcher: Fetcher, endpoint: str, body: dict[str, Any], page_size: int, max_pages: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if page_size <= 0 or max_pages <= 0:
        raise ValueError("Размер страницы и число страниц должны быть положительными")
    rows: list[dict[str, Any]] = []
    offset = 0
    complete = False
    pages = 0
    for _ in range(max_pages):
        request = {**body, "limit": page_size, "offset": offset}
        response = fetcher(endpoint, request)
        if not isinstance(response, dict):
            raise ValueError("Ответ страницы должен быть объектом")
        data = response.get("data")
        if not isinstance(data, list):
            raise ValueError("Ответ страницы не содержит массив data")
        if any(not isinstance(item, dict) for item in data):
            raise ValueError("Строка страницы должна быть объектом")
        pages += 1
        rows.extend(data)
        total = response.get("total")
        offset += len(data)
        if not data or len(data) < page_size or (isinstance(total, int) and offset >= total):
            complete = True
            break
        if len(data) == 0:
            break
    return rows, {"status": "complete" if complete else "partial", "pages": pages, "objects": len(rows), "complete": complete}


def flatten_analytics(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("data")
    if not isinstance(data, list):
        raise ValueError("analytics/data не содержит массив data")
    rows: list[dict[str, Any]] = []
    for block in data:
        if not isinstance(block, dict):
            raise ValueError("Блок analytics/data должен быть объектом")
        for item in block.get("items") or []:
            if not isinstance(item, dict):
                raise ValueError("Строка analytics/data должна быть объектом")
            row: dict[str, Any] = {}
            dimensions = item.get("dimensions") or {}
            if isinstance(dimensions, dict):
                for name, meta in dimensions.items():
                    row[f"dimension_{name}"] = meta.get("value") if isinstance(meta, dict) else meta
            for metric in item.get("metrics") or []:
                if not isinstance(metric, dict):
                    continue
                name = str(metric.get("metric_name") or metric.get("id") or "metric")
                attribution = str(metric.get("attribution_model_id") or "default")
                row[f"{name}__{attribution}"] = metric.get("value")
            rows.append(row)
    return rows


def number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def total_metric(rows: list[dict[str, Any]], prefix: str) -> float:
    return sum(number(value) for row in rows for key, value in row.items() if key == prefix or key.startswith(prefix + "__"))


def reconciliation(analytics_rows: list[dict[str, Any]], order_rows: list[dict[str, Any]]) -> dict[str, float]:
    analytics_sales = total_metric(analytics_rows, "sales")
    analytics_revenue = total_metric(analytics_rows, "revenue")
    raw_sales = float(len(order_rows))
    raw_revenue = sum(number(row.get("revenue")) for row in order_rows)
    return {
        "analytics_sales": analytics_sales,
        "raw_sales": raw_sales,
        "sales_difference": raw_sales - analytics_sales,
        "analytics_revenue": analytics_revenue,
        "raw_revenue": raw_revenue,
        "revenue_difference": raw_revenue - analytics_revenue,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credentials-file")
    parser.add_argument("--from", dest="date_from", required=True)
    parser.add_argument("--to", dest="date_to", required=True)
    parser.add_argument("--report-name", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dimension", action="append", default=[])
    parser.add_argument("--metric", action="append", default=[])
    parser.add_argument("--attribution", default="default")
    parser.add_argument("--channel", default="all")
    parser.add_argument("--currency", default="account_currency")
    parser.add_argument("--filters-json")
    parser.add_argument("--include-personal-data", action="store_true")
    parser.add_argument("--include-orders", action="store_true")
    parser.add_argument("--include-call-tracking", action="store_true")
    parser.add_argument("--call-tracking-endpoint")
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--max-pages", type=int, default=100)
    args = parser.parse_args()
    if (args.include_orders or args.include_call_tracking) and not args.include_personal_data:
        parser.error("Сырые сделки и коллтрекинг требуют явного --include-personal-data")
    if args.include_call_tracking and not args.call_tracking_endpoint:
        parser.error("Для коллтрекинга нужен явно проверенный --call-tracking-endpoint")
    project, api_key, base_url = load_access(Path(args.credentials_file).expanduser().resolve() if args.credentials_file else None)
    output = Path(args.output_dir).expanduser().resolve()
    private_dir(output)
    filters = json.loads(Path(args.filters_json).read_text(encoding="utf-8")) if args.filters_json else []
    context = {
        "report_name": args.report_name,
        "period": {"from": args.date_from, "to": args.date_to},
        "window": f"{args.date_from}..{args.date_to}",
        "attribution": args.attribution,
        "channel": args.channel,
        "filters": filters,
        "currency": args.currency,
        "collected_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    request = {
        "dimensions": args.dimension or ["marker_level_1", "marker_level_2", "marker_level_3"],
        "metrics": args.metric or DEFAULT_METRICS,
        "period": context["period"],
        "filters": filters,
        "attribution": args.attribution,
    }
    fetcher: Fetcher = lambda endpoint, body: api_call(base_url, project, api_key, endpoint, body)
    analytics_response = fetcher("project/analytics/data", request)
    analytics_rows = flatten_analytics(analytics_response)
    sources: dict[str, Any] = {
        "analytics_report": {"status": "complete", "objects": len(analytics_rows), "required": True},
        "raw_orders": {"status": "not_requested", "objects": 0, "required": args.include_orders},
        "call_tracking": {"status": "not_requested", "objects": 0, "required": args.include_call_tracking},
    }
    atomic_json(output / "report-context.json", context)
    atomic_json(output / "analytics-request.json", request)
    atomic_json(output / "analytics-response.json", analytics_response)
    atomic_tsv(output / "analytics-rows.tsv", analytics_rows)
    order_rows: list[dict[str, Any]] = []
    if args.include_orders:
        order_rows, state = paginate(fetcher, "project/integration/order/list", {"extend": ["visit"]}, args.page_size, args.max_pages)
        sources["raw_orders"] = {**state, "required": True}
        atomic_json(output / "orders-raw.json", {"data": order_rows})
        atomic_tsv(output / "orders-rows.tsv", order_rows)
    if args.include_call_tracking:
        calls, state = paginate(fetcher, args.call_tracking_endpoint, {}, args.page_size, args.max_pages)
        sources["call_tracking"] = {**state, "required": True}
        atomic_json(output / "call-tracking-raw.json", {"data": calls})
        atomic_tsv(output / "call-tracking-rows.tsv", calls)
    differences = reconciliation(analytics_rows, order_rows) if args.include_orders else {"status": "not_available_without_raw_orders"}
    atomic_json(output / "reconciliation.json", {"context": context, "values": differences})
    required_complete = all(source["status"] == "complete" for source in sources.values() if source["required"])
    summary = {"status": "complete" if required_complete else "partial", "sources": sources, "context": context, "reconciliation": differences}
    atomic_json(output / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "analytics_rows": len(analytics_rows), "orders_rows": len(order_rows)}, ensure_ascii=False))
    return 0 if required_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
