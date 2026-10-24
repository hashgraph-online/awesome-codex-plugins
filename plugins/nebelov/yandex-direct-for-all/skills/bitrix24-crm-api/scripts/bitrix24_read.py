#!/usr/bin/env python3
"""Только чтение Битрикс24 через входящий вебхук.

  probe                 доступ и скоупы вебхука (адрес не печатается)
  schema --out DIR      воронки, стадии, статусы, источники, поля лидов и сделок
  export --entity ...   полная выгрузка с манифестом (лиды, сделки, дела, история стадий, звонки)

Адрес вебхука: переменная BITRIX24_WEBHOOK_URL (звонки — BITRIX24_TELEPHONY_WEBHOOK_URL, если у основного
нет скоупа telephony) или закрытый JSON 0600 {"webhook_url": "..."} через --access-file. Вызываются только
методы чтения из белого списка; телефоны и имена выгружаются только с --include-personal-data.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

READ_ONLY = {
    "scope", "batch", "crm.item.list", "crm.item.fields", "crm.lead.list", "crm.lead.fields", "crm.lead.userfield.list",
    "crm.deal.list", "crm.deal.fields", "crm.deal.userfield.list", "crm.status.list", "crm.status.entity.types",
    "crm.category.list", "crm.dealcategory.list", "crm.stagehistory.list", "crm.activity.list", "crm.contact.list",
    "voximplant.statistic.get", "user.get",
}
PAUSE = 0.5  # не меньше 0,5 с между запросами (лимит облака — 2 запроса в секунду)
PERSONAL = {"PHONE", "EMAIL", "NAME", "LAST_NAME", "SECOND_NAME", "IM", "ADDRESS", "PHONE_NUMBER", "CALLER_ID"}
ENTITIES = {
    "lead": ("crm.lead.list", ["ID", "DATE_CREATE", "STATUS_ID", "SOURCE_ID", "SOURCE_DESCRIPTION", "ASSIGNED_BY_ID",
                               "UTM_SOURCE", "UTM_MEDIUM", "UTM_CAMPAIGN", "UTM_CONTENT", "UTM_TERM", "OPPORTUNITY"], "DATE_CREATE"),
    "deal": ("crm.deal.list", ["ID", "DATE_CREATE", "CLOSEDATE", "CATEGORY_ID", "STAGE_ID", "STAGE_SEMANTIC_ID", "LEAD_ID",
                               "CONTACT_ID", "OPPORTUNITY", "CURRENCY_ID", "SOURCE_ID", "UTM_SOURCE", "UTM_MEDIUM",
                               "UTM_CAMPAIGN", "UTM_CONTENT", "UTM_TERM"], "DATE_CREATE"),
    "activity": ("crm.activity.list", ["ID", "CREATED", "TYPE_ID", "DIRECTION", "OWNER_TYPE_ID", "OWNER_ID", "ORIGIN_ID",
                                       "PROVIDER_ID"], "CREATED"),
    "stagehistory": ("crm.stagehistory.list", ["ID", "CREATED_TIME", "TYPE_ID", "OWNER_ID", "STAGE_ID", "STATUS_ID"],
                     "CREATED_TIME"),
    "call": ("voximplant.statistic.get", ["ID", "CALL_START_DATE", "CALL_TYPE", "CALL_DURATION", "PORTAL_NUMBER",
                                          "CRM_ENTITY_TYPE", "CRM_ENTITY_ID", "CRM_ACTIVITY_ID"], "CALL_START_DATE"),
}


def webhook(args: argparse.Namespace, telephony: bool = False) -> str:
    if telephony and os.environ.get("BITRIX24_TELEPHONY_WEBHOOK_URL"):
        url = os.environ["BITRIX24_TELEPHONY_WEBHOOK_URL"]
        if not url.startswith("https://") or "/rest/" not in url:
            raise ValueError("BITRIX24_TELEPHONY_WEBHOOK_URL должен начинаться с https:// и содержать /rest/.")
        return url.rstrip("/") + "/"
    url = os.environ.get("BITRIX24_WEBHOOK_URL", "")
    if not url and args.access_file:
        path = Path(args.access_file).expanduser()
        if path.stat().st_mode & 0o077:
            raise ValueError("Файл доступа должен иметь права 0600.")
        url = str(json.loads(path.read_text(encoding="utf-8")).get("webhook_url", ""))
    if not url.startswith("https://") or "/rest/" not in url:
        raise ValueError("Нет адреса вебхука: задайте BITRIX24_WEBHOOK_URL или --access-file.")
    return url.rstrip("/") + "/"


def mask(text: str, base: str) -> str:
    """Убирает из текста ошибки адрес вебхука и его секретную часть пути."""
    secret = base.split("/rest/", 1)[-1].strip("/")
    for part in [base, base.rstrip("/"), secret, *[p for p in secret.split("/") if len(p) >= 6]]:
        if part:
            text = text.replace(part, "***")
    return text


def call(base: str, method: str, params: dict | None = None, retries: int = 5) -> dict:
    """Один вызов чтения с повтором при лимитах; адрес вебхука в ошибки не попадает."""
    if method not in READ_ONLY:
        raise ValueError(f"Метод {method} не входит в белый список чтения.")
    if method == "batch":
        for command in (params or {}).get("cmd", {}).values():
            if command.split("?")[0] not in READ_ONLY or command.split("?")[0] == "batch":
                raise ValueError("В batch разрешены только методы чтения, вложенный batch запрещён.")
    body = json.dumps(params or {}).encode()
    for attempt in range(retries):
        request = urllib.request.Request(base + method + ".json", data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as error:
            text = mask(error.read().decode("utf-8", "replace"), base)  # маскировать до любой обрезки
            if error.code in (429, 503) or "QUERY_LIMIT_EXCEEDED" in text or "OPERATION_TIME_LIMIT" in text:
                time.sleep(2 * (attempt + 1))
                continue
            try:
                detail = json.loads(text)
                text = f"{detail.get('error')}: {detail.get('error_description', '')}"
            except ValueError:
                text = text[:200]
            raise RuntimeError(mask(f"{method}: HTTP {error.code} {text}", base)) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(2 * (attempt + 1))
            continue
        if "error" in data:
            raise RuntimeError(mask(f"{method}: {data.get('error')} {data.get('error_description', '')}", base))
        return data
    raise RuntimeError(f"{method}: не ответил после {retries} попыток")


def list_by_id(base: str, method: str, params: dict) -> tuple[list[dict], int]:
    """Полный обход по ID (>ID, start=-1): без подсчёта total и без пропусков при сдвиге страниц."""
    rows, pages, last_id = [], 0, 0
    while True:
        query = json.loads(json.dumps(params))
        query.setdefault("filter", {})[">ID"] = last_id
        query["order"] = {"ID": "ASC"}
        query["start"] = -1
        result = call(base, method, query)["result"]
        batch = result.get("items", result) if isinstance(result, dict) else result
        pages += 1
        rows.extend(batch)
        if len(batch) < 50:
            return rows, pages
        last = batch[-1].get("ID") or batch[-1].get("id")
        if last is None:
            raise RuntimeError(f"{method}: строка без ID — обход по ID невозможен, выгрузка неполная.")
        last_id = int(last)
        time.sleep(PAUSE)


def list_paged(base: str, method: str, params: dict) -> tuple[list[dict], int]:
    """Обход через start/next — для методов без фильтра по ID (статистика звонков)."""
    rows, pages, start = [], 0, 0
    while True:
        data = call(base, method, {**params, "start": start})
        result = data["result"]
        if isinstance(result, dict):
            result = result.get("items", result.get("categories", result))
        rows.extend(result)
        pages += 1
        if "next" not in data:
            return rows, pages
        start = data["next"]
        time.sleep(PAUSE)


def save(path: Path, payload) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    os.chmod(path, 0o600)


def cmd_probe(args: argparse.Namespace) -> dict:
    base = webhook(args)
    scopes = call(base, "scope")["result"]
    types = call(base, "crm.status.entity.types")["result"]
    return {"webhook": "найден", "scopes": scopes, "crm_status_types": len(types),
            "telephony": "telephony" in scopes or bool(os.environ.get("BITRIX24_TELEPHONY_WEBHOOK_URL"))}


def cmd_schema(args: argparse.Namespace) -> dict:
    base, out = webhook(args), Path(args.out)
    categories = list_paged(base, "crm.category.list", {"entityTypeId": 2})[0]
    statuses = list_paged(base, "crm.status.list", {})[0]
    snapshot = {"deal_categories": categories, "statuses": statuses,
                "lead_fields": call(base, "crm.lead.fields")["result"],
                "deal_fields": call(base, "crm.deal.fields")["result"],
                "lead_userfields": list_paged(base, "crm.lead.userfield.list", {})[0],
                "deal_userfields": list_paged(base, "crm.deal.userfield.list", {})[0]}
    save(out / "schema.json", snapshot)
    # crm.category.list уже содержит основную воронку (isDefault=Y), единица не прибавляется.
    return {"file": str(out / "schema.json"), "deal_categories": len(categories),
            "statuses": len(statuses), "status_groups": sorted({s.get("ENTITY_ID") for s in statuses})}


def cmd_export(args: argparse.Namespace) -> dict:
    method, fields, date_field = ENTITIES[args.entity]
    if args.fields:
        fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    if not args.include_personal_data:
        fields = [f for f in fields if f.upper() not in PERSONAL]
    if "ID" not in fields:
        fields = ["ID", *fields]  # обход по ID и проверка полноты без ID невозможны
    out = Path(args.out)
    for stale in (out / f"{args.entity}.json", out / f"{args.entity}.manifest.json"):
        if stale.exists():
            stale.unlink()  # прошлая выгрузка не должна остаться на месте, если эта упадёт на любом шаге
    base = webhook(args, telephony=args.entity == "call")
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    period = {f">={date_field}": args.since, f"<{date_field}": args.until}
    if args.entity == "call":
        rows, pages = list_paged(base, method, {"FILTER": period, "SORT": "ID", "ORDER": "ASC"})
    elif args.entity == "stagehistory":
        rows, pages = list_by_id(base, method, {"entityTypeId": 2 if args.stagehistory_of == "deal" else 1,
                                                "filter": period, "select": fields})
    else:
        rows, pages = list_by_id(base, method, {"filter": period, "select": fields})
    # Сохраняются только объявленные поля: метод может вернуть всё (комментарии, ссылки на записи звонков).
    # Личные поля сохраняются только при явном флаге и только если названы в --fields.
    keep = {f.upper() for f in fields if args.include_personal_data or f.upper() not in PERSONAL}
    rows = [{k: v for k, v in row.items() if k.upper() in keep} for row in rows]
    ids = [str(row.get("ID") or row.get("id") or "") for row in rows]
    complete = all(ids) and len(ids) == len(set(ids))
    manifest = {"entity": args.entity, "method": method, "filter": period, "fields": fields, "rows": len(rows),
                "unique_ids": len(set(ids)), "pages": pages, "complete": complete,
                "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "timezone_note": "даты REST — в часовом поясе портала", "personal_data": args.include_personal_data}
    save(out / f"{args.entity}.json", rows)
    save(out / f"{args.entity}.manifest.json", manifest)
    if not manifest["complete"]:
        raise RuntimeError("В выгрузке повторяются или отсутствуют ID: она неполная, отчёт по ней строить нельзя.")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("probe", "schema", "export"))
    parser.add_argument("--access-file", help="закрытый JSON 0600 с полем webhook_url")
    parser.add_argument("--out", default="bitrix24-export")
    parser.add_argument("--entity", choices=sorted(ENTITIES), default="lead")
    parser.add_argument("--since", help="начало периода, ISO, включительно (например 2026-10-01T00:00:00+03:00)")
    parser.add_argument("--until", help="конец периода, ISO, не включительно")
    parser.add_argument("--fields", help="свой список полей через запятую (UF_* и UTM_* называть явно)")
    parser.add_argument("--stagehistory-of", choices=("lead", "deal"), default="deal")
    parser.add_argument("--include-personal-data", action="store_true", help="выгружать телефоны, почту и имена")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "export" and not (args.since and args.until):
        raise ValueError("Для export нужны --since и --until.")
    result = {"probe": cmd_probe, "schema": cmd_schema, "export": cmd_export}[args.command](args)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    os.umask(0o077)
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)
