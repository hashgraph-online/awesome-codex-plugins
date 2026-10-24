#!/usr/bin/env python3
"""Сбор выдачи Яндекса и Google и частотностей Wordstat через XMLRiver.

Команды:
  info      баланс, цены и потоки аккаунта (get_info), секреты не печатаются;
  plan      разбор заданий без сети: число запросов, оценка цены, SHA-256 плана;
  collect   платный сбор по одобренному плану с потолком стоимости и журналом;
  export    таблицы из сохранённых ответов, без сети;
  inflight  задания с неизвестным исходом; сверка и ручное снятие.

Скрипт собирает сырые данные и не принимает смысловых решений: не выбирает
ключи, не переходит по рекламным ссылкам и не открывает посадочные страницы.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import tempfile
import time
import urllib.parse
import uuid
import xml.etree.ElementTree as ET
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

SCHEMA_VERSION = "xmlriver-collect-v1"
SKILL_DIR = Path(__file__).resolve().parents[1]
DEMO_FILE = SKILL_DIR / "config" / "xmlriver_demo_access.json"
DEMO_MAX_COST = Decimal("2")
URLS = {
    "yandex": "https://xmlriver.com/search_yandex/xml",
    "google": "https://xmlriver.com/search/xml",
    "wordstat": "https://xmlriver.com/wordstat/new/json",
}
INFO_URL = "https://xmlriver.com/api/get_info/"
EMPTY = {"15"}
TEMPORARY = {"101", "110", "111", "500"}
STOP_BATCH = {"31", "42", "45", "115", "200"}
RESULT_HEADER = [
    "job_id", "layer", "purpose", "search_query", "search_region", "region_id", "page", "group_rank",
    "doc_rank", "result_rank", "result_title_or_snippet", "result_title", "result_headline",
    "result_domain", "source_url", "collected_at", "raw_json_path", "raw_xml_path", "notes",
]
AD_RESULT_HEADER = [
    "job_id", "layer", "purpose", "search_query", "search_region", "region_id", "page", "group_rank",
    "doc_rank", "result_rank", "result_title_or_snippet", "result_title", "result_headline",
    "result_domain", "source_url", "collected_at", "raw_json_path", "raw_html_path", "notes",
    "serp_position", "ad_position", "count_url",
]
SERP_EXTRA = ["provider", "engine", "device", "contenttype", "abs_rank_state", "job_key", "raw_sha256", "corrected_query"]
AD_EXTRA = ["provider", "engine", "block", "adsurl", "title_clean", "snippet_clean", "sitelinks_json",
            "landing_status", "landing_url", "job_key", "raw_sha256"]
MSK = timezone(timedelta(hours=3))  # даты Wordstat — по Москве
FALSEY = {"0", "false", "no", "off", "disabled"}
OPEN_DBS: list[sqlite3.Connection] = []


class StopBatch(Exception):
    """Ошибка, после которой пакет нельзя продолжать (доступ, баланс, перегрузка)."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------- доступ ----------

def read_key_values(path: Path) -> dict[str, str]:
    if path.stat().st_mode & 0o077:
        raise ValueError(f"Файл доступа {path.name} должен иметь права 0600.")
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        return {"XMLRIVER_USER": str(data.get("user", "")), "XMLRIVER_KEY": str(data.get("key", ""))}
    except ValueError:
        pass
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip().removeprefix("export ").strip()] = value.strip().strip("'\"")
    return values


def credentials(args: argparse.Namespace) -> tuple[dict[str, str], bool]:
    values = {"XMLRIVER_USER": os.environ.get("XMLRIVER_USER") or os.environ.get("XMLRIVER_USER_ID", ""),
              "XMLRIVER_KEY": os.environ.get("XMLRIVER_KEY", "")}
    path = args.credentials_file or os.environ.get("XMLRIVER_CREDENTIALS_FILE")
    if not (values["XMLRIVER_USER"] and values["XMLRIVER_KEY"]) and path:
        found = read_key_values(Path(path).expanduser())
        values = {"XMLRIVER_USER": found.get("XMLRIVER_USER") or found.get("XMLRIVER_USER_ID", ""),
                  "XMLRIVER_KEY": found.get("XMLRIVER_KEY", "")}
    if values["XMLRIVER_USER"] and values["XMLRIVER_KEY"]:
        return {"user": values["XMLRIVER_USER"], "key": values["XMLRIVER_KEY"]}, False
    if getattr(args, "use_demo_key", False):
        demo = json.loads(DEMO_FILE.read_text(encoding="utf-8"))
        return {"user": str(demo["user"]), "key": str(demo["key"])}, True
    raise ValueError("Нет доступа XMLRiver: задайте XMLRIVER_USER и XMLRIVER_KEY, --credentials-file "
                     "или для короткой пробы --use-demo-key.")


def redact_bytes(body: bytes, auth: dict[str, str]) -> bytes:
    """Затирает ключ везде, а номер пользователя — только как параметр user=: голые цифры номера
    могут совпасть с частотностями и кодами ответа, их трогать нельзя."""
    if auth.get("key"):
        body = body.replace(auth["key"].encode(), b"[REDACTED]")
    if auth.get("user"):
        user = re.escape(auth["user"].encode())
        body = re.sub(rb"(user=)" + user + rb"(?![0-9])", rb"\1[REDACTED]", body)
    return body


def redact(text: str, auth: dict[str, str]) -> str:
    return redact_bytes(text.encode("utf-8"), auth).decode("utf-8")


def get_info(auth: dict[str, str]) -> dict:
    url = INFO_URL + "?" + urllib.parse.urlencode(auth)
    try:
        with urlopen(url, timeout=60) as response:
            return json.load(response)
    except (HTTPError, URLError, OSError, ValueError) as error:
        raise ValueError(f"get_info не ответил: {type(error).__name__}") from None


# ---------- задания ----------

def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return [{(k or "").strip(): (v or "").strip() for k, v in row.items()}
                for row in csv.DictReader(stream, delimiter="\t")]


def serp_jobs(args: argparse.Namespace) -> list[dict]:
    rows = read_tsv(Path(args.jobs_file))
    if not rows:
        raise ValueError("Файл заданий пуст.")
    for column in ("job_id", "search_query"):
        if column not in rows[0]:
            raise ValueError(f"В файле заданий нет колонки {column}.")
    jobs, seen = [], set()
    for row in rows:
        if row.get("enabled", "1").lower() in FALSEY:
            continue
        if not row["search_query"]:
            raise ValueError(f"Пустой search_query в задании {row['job_id']}.")
        if row["job_id"] in seen:
            raise ValueError(f"job_id повторяется: {row['job_id']}.")
        seen.add(row["job_id"])
        engines = [row.get("engine") or args.engine]
        engines = ["yandex", "google"] if engines == ["both"] else engines
        pages = [int(row["page"])] if row.get("page") else list(range(args.pages))
        for engine in engines:
            if engine not in ("yandex", "google"):
                raise ValueError(f"Неизвестная система {engine} в задании {row['job_id']}.")
            for page in pages:
                params = {"query": row["search_query"], "device": row.get("device") or args.device,
                          "groupby": 10, "ai": 1 if args.ai else 0}
                if engine == "yandex":
                    region = row.get("region_id") or "225"
                    if not region.isdigit():
                        raise ValueError(f"region_id должен быть числом (задание {row['job_id']}).")
                    params.update(lr=region, page=page, domain="ru", lang="ru")
                    if args.ads == "on":
                        blocks = ["y_topads", "y_bottomads"] + (["y_rightads"] if args.yandex_right_ads else [])
                        params.update(ads=1, additional=",".join(blocks))
                else:
                    params.update(page=page + 1, country=row.get("google_country") or args.google_country,
                                  lr=row.get("google_lang") or args.google_lang)
                    loc = row.get("google_loc") or args.google_loc
                    domain = row.get("google_domain") or args.google_domain
                    if loc:
                        params["loc"] = loc
                    if domain:
                        params["domain"] = domain
                    if args.ads == "on":
                        params.update(ads=1, additional="topads,bottomads")
                effective = dict(row)
                if engine == "yandex":
                    effective["region_id"] = params["lr"]
                else:
                    effective["region_id"] = params.get("loc") or f"country:{params['country']}"
                effective["search_region"] = row.get("search_region") or effective["region_id"]
                jobs.append({"kind": "serp", "engine": engine, "params": params, "page": page,
                             "row": {k: effective.get(k, "") for k in ("job_id", "layer", "purpose", "search_query",
                                                                        "search_region", "region_id", "notes")}})
    return finish_jobs(jobs)


def read_masks(path: Path) -> list[str]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if lines and "\t" in lines[0] and "mask" in [c.strip().lower() for c in lines[0].split("\t")]:
        index = [c.strip().lower() for c in lines[0].split("\t")].index("mask")
        masks = [line.split("\t")[index] for line in lines[1:] if len(line.split("\t")) > index]
    else:
        masks = [line.split("\t")[0] for line in lines if not line.startswith("#") and line.strip().lower() != "mask"]
    masks = [re.sub(r"\s+", " ", m).strip() for m in masks if m.strip()]
    if not masks:
        raise ValueError("В файле масок нет ни одной маски.")
    return list(dict.fromkeys(masks))


def history_range(args: argparse.Namespace) -> tuple[str, str]:
    if args.start and args.end:
        start = datetime.strptime(args.start, "%d.%m.%Y").date()
        end = datetime.strptime(args.end, "%d.%m.%Y").date()
    else:
        first_this_month = date.today().replace(day=1)
        end = first_this_month - timedelta(days=1)
        start = (end.replace(day=1) - timedelta(days=150)).replace(day=1)
    if end >= date.today():
        raise ValueError("Конец периода динамики не может быть сегодня или позже.")
    if args.period == "month" and (start.day != 1 or (end + timedelta(days=1)).day != 1
                                   or (end.year - start.year) * 12 + end.month - start.month < 2):
        raise ValueError("Для month нужен период от 3 полных месяцев: с первого по последнее число.")
    if args.period == "week" and (start.weekday() != 0 or end.weekday() != 6 or (end - start).days < 20):
        raise ValueError("Для week нужно от 3 недель: с понедельника по воскресенье.")
    if args.period == "day" and (end - start).days < 2:
        raise ValueError("Для day нужно не меньше 3 дней.")
    return start.strftime("%d.%m.%Y"), end.strftime("%d.%m.%Y")


def wordstat_jobs(args: argparse.Namespace) -> list[dict]:
    masks = read_masks(Path(args.masks_file))
    regions = [r.strip() for r in args.regions.split(",") if r.strip()] or [""]
    devices = "" if args.devices == "all" else ",".join(
        "phone" if d in ("mobile", "smartphone") else d for d in args.devices.split(","))
    pagetypes = [p.strip() for p in args.pagetypes.split(",") if p.strip()]
    if any(p not in ("words", "history") for p in pagetypes):
        raise ValueError("--pagetypes допускает только words и history.")
    start, end = history_range(args) if "history" in pagetypes else ("", "")
    jobs = []
    for mask in masks:
        for region in regions:
            for pagetype in pagetypes:
                params = {"query": mask, "pagetype": pagetype}
                if region:
                    params["regions"] = region
                if devices:
                    params["device"] = devices
                if pagetype == "history":
                    params.update(period=args.period, start=start, end=end)
                jobs.append({"kind": "wordstat", "engine": "wordstat", "params": params, "page": 0,
                             "row": {"mask": mask, "region": region, "devices": args.devices, "pagetype": pagetype}})
    return finish_jobs(jobs)


def finish_jobs(jobs: list[dict]) -> list[dict]:
    keys = set()
    for job in jobs:
        identity = json.dumps([SCHEMA_VERSION, job["kind"], job["engine"], job["params"]],
                              sort_keys=True, ensure_ascii=False)
        job["job_key"] = sha256(identity.encode())[:32]
        if job["job_key"] in keys:
            raise ValueError(f"Одинаковые задания в плане: {job['params'].get('query')}.")
        keys.add(job["job_key"])
    return jobs


def ai_extra_per_request(args: argparse.Namespace) -> Decimal:
    """Надбавка за ai=1 на один запрос; число конечное и неотрицательное."""
    if not args.ai:
        return Decimal(0)
    if not args.ai_price_per_1000:
        raise ValueError("Для --ai укажите --ai-price-per-1000 — надбавку по тарифу: get_info её не сообщает, "
                         "без неё потолок стоимости не проверить.")
    try:
        price = Decimal(args.ai_price_per_1000)
    except ArithmeticError:
        raise ValueError("--ai-price-per-1000 должно быть числом.") from None
    if not price.is_finite() or price < 0:
        raise ValueError("--ai-price-per-1000 должно быть конечным неотрицательным числом.")
    return price / 1000


def plan_sha(kind: str, jobs: list[dict]) -> str:
    return sha256(json.dumps({"schema": SCHEMA_VERSION, "kind": kind,
                              "jobs": [j["job_key"] for j in jobs]}).encode())


# ---------- журнал ----------

def open_db(run: Path, create: bool) -> sqlite3.Connection | None:
    path = run / "journal.sqlite3"
    if not create and not path.exists():
        return None
    run.mkdir(mode=0o700, parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    OPEN_DBS.append(db)
    os.chmod(path, 0o600)
    db.execute("PRAGMA journal_mode=DELETE")
    db.execute("""CREATE TABLE IF NOT EXISTS jobs (job_key TEXT PRIMARY KEY, kind TEXT, engine TEXT,
        spec_json TEXT NOT NULL, status TEXT NOT NULL, success_attempt INTEGER, last_error_code TEXT)""")
    db.execute("""CREATE TABLE IF NOT EXISTS attempts (attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_key TEXT NOT NULL, started_utc TEXT NOT NULL, finished_utc TEXT, http_status INTEGER,
        error_code TEXT, error_text TEXT, failure_class TEXT, raw_file TEXT NOT NULL, raw_sha256 TEXT)""")
    db.commit()
    return db


def statuses(db: sqlite3.Connection | None, jobs: list[dict]) -> dict[str, str]:
    found = dict(db.execute("SELECT job_key,status FROM jobs")) if db else {}
    return {j["job_key"]: found.get(j["job_key"], "pending") for j in jobs}


def write_atomic(path: Path, body: bytes) -> Path:
    """Атомарно создаёт файл; существующий оплаченный ответ не перезаписывается."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp, path)
        except FileExistsError:
            path = path.with_name(f"{path.stem}-collision-{uuid.uuid4().hex}{path.suffix}")
            os.link(temp, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return path


def fetch_and_store(job: dict, auth: dict[str, str], raw_path: Path, timeout: int) -> dict:
    """Рабочий поток: сеть и файлы, без SQLite. Тексты ошибок не содержат адресов с ключом."""
    url = URLS[job["engine"]] + "?" + urllib.parse.urlencode({**auth, **job["params"]})
    try:
        try:
            with urlopen(url, timeout=timeout) as response:
                status, body = response.status, response.read()
        except HTTPError as error:
            status, body = error.code, error.read()
    except (URLError, OSError, ValueError) as error:
        return {"failure_class": type(error).__name__, "raw_path": None, "http_status": None}
    clean = redact_bytes(body, auth)
    path = write_atomic(raw_path, clean)
    write_atomic(Path(str(path) + ".meta.json"),
                 json.dumps({"http_status": status, "sha256": sha256(clean)}).encode())
    return {"failure_class": "response_redacted" if clean != body else None, "raw_path": path, "http_status": status}


def parse_response(kind: str, body: bytes, status: int | None, pagetype: str | None = None) -> dict:
    """Возвращает {error_code, error_text, ...}; код ошибки — строкой."""
    if kind == "wordstat":
        data = json.loads(body.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("ответ Wordstat не объект JSON")
        if "error" in data or ("code" in data and "popular" not in data and "graph" not in data):
            return {"error_code": str(data.get("code", "unknown")), "error_text": str(data.get("error", ""))[:300]}
        # Проверяется поле, которое ждёт именно это задание: words — popular, history — graph.
        if pagetype == "history":
            if not isinstance(data.get("graph"), dict):
                raise ValueError("в ответе history нет graph")
        elif not isinstance(data.get("popular"), list) or not isinstance(data.get("associations", []), list):
            raise ValueError("в ответе words нет списка popular")
        return {"error_code": None, "data": data}
    root = ET.fromstring(body)
    response = root.find("response")
    if root.tag != "yandexsearch" or response is None:
        raise ValueError("неожиданный корень XML")
    error = response.find("error")
    if error is not None:
        return {"error_code": error.get("code") or "unknown", "error_text": (error.text or "").strip()[:300]}
    docs = response.findall("./results/grouping/group/doc")
    organic = [d for d in docs if (d.findtext("contenttype") or "organic").strip() == "organic"]
    ads = [(block, item) for block in ("topads", "bottomads", "rightads") for item in response.findall(f"./{block}/query")]
    return {"error_code": None, "organic": organic, "features": [d for d in docs if d not in organic], "ads": ads,
            "corrected": (response.findtext("correct") or "").strip()}


def classify(parsed: dict | None, status: int | None) -> str:
    if parsed is None:
        return "error"
    code = parsed.get("error_code")
    if code in EMPTY:
        return "empty"
    if code or status == 429 or (status or 0) >= 400:
        return "error"
    return "success"


def finalize(db: sqlite3.Connection, run: Path, job: dict, attempt_id: int, outcome: dict, auth: dict) -> str:
    path, status = outcome["raw_path"], outcome["http_status"]
    if path is None:
        return "inflight"  # Исход неизвестен: ответ мог быть оплачен. Автоповтора нет.
    body = path.read_bytes()
    meta = json.loads(Path(str(path) + ".meta.json").read_text(encoding="utf-8"))
    if meta["sha256"] != sha256(body) or meta["http_status"] != status:
        return "inflight"
    try:
        parsed = parse_response(job["kind"], body, status, job["params"].get("pagetype"))
        failure = outcome["failure_class"]
    except (ET.ParseError, ValueError, UnicodeDecodeError):
        parsed, failure = None, "response_unparseable"
    state = classify(parsed, status)
    code = (parsed or {}).get("error_code") or ("429" if status == 429 else None)
    with db:
        db.execute("""UPDATE attempts SET finished_utc=?,http_status=?,error_code=?,error_text=?,failure_class=?,
            raw_file=?,raw_sha256=? WHERE attempt_id=?""",
                   (utc_now(), status, code, redact((parsed or {}).get("error_text") or "", auth), failure,
                    str(path.relative_to(run)), sha256(body), attempt_id))
        db.execute("UPDATE jobs SET status=?,success_attempt=?,last_error_code=? WHERE job_key=?",
                   (state, attempt_id if state in ("success", "empty") else None, code, job["job_key"]))
    if code in STOP_BATCH or status == 429:
        raise StopBatch(f"XMLRiver вернул код {code or status}: пакет остановлен.")
    return state


def recover_saved(db: sqlite3.Connection, run: Path, jobs_by_key: dict, auth: dict) -> int:
    """Закрывает незавершённые попытки по сохранённому ответу и квитанции, без сети."""
    recovered = 0
    rows = list(db.execute("SELECT attempt_id,job_key,raw_file FROM attempts WHERE finished_utc IS NULL"))
    for attempt_id, job_key, rel in rows:
        if job_key not in jobs_by_key:
            continue
        base = run / rel
        candidates = [p for p in [base, *base.parent.glob(f"{base.stem}-collision-*{base.suffix}")]
                      if p.exists() and Path(str(p) + ".meta.json").exists()]
        if len(candidates) != 1:
            continue
        status = json.loads(Path(str(candidates[0]) + ".meta.json").read_text(encoding="utf-8"))["http_status"]
        try:
            finalize(db, run, jobs_by_key[job_key], attempt_id,
                     {"raw_path": candidates[0], "http_status": status, "failure_class": None}, auth)
        except StopBatch:
            pass
        recovered += 1
    return recovered


def start_attempt(db: sqlite3.Connection, run: Path, job: dict) -> tuple[int, Path] | None:
    """Захватывает задание атомарно: только из pending или error. Иначе None — запрос не отправляется."""
    suffix = ".json" if job["kind"] == "wordstat" else ".xml"
    with db:
        claimed = db.execute("UPDATE jobs SET status='inflight' WHERE job_key=? AND status IN ('pending','error')",
                             (job["job_key"],)).rowcount
        if claimed != 1:
            return None
        number = db.execute("SELECT COUNT(*) FROM attempts WHERE job_key=?", (job["job_key"],)).fetchone()[0] + 1
        rel = f"raw/{job['job_key']}-{number:03d}{suffix}"
        cursor = db.execute("INSERT INTO attempts(job_key,started_utc,raw_file) VALUES(?,?,?)",
                            (job["job_key"], utc_now(), rel))
    return cursor.lastrowid, run / rel


def collect(db: sqlite3.Connection, run: Path, queue: list[dict], auth: dict, workers: int, timeout: int) -> dict:
    """Главный поток владеет SQLite; рабочие потоки только ходят в сеть и пишут файлы."""
    counts = {"success": 0, "empty": 0, "error": 0, "inflight": 0, "started": 0, "skipped_claimed": 0}
    pending, active, stop = iter(queue), {}, None
    with ThreadPoolExecutor(max_workers=workers) as pool:
        def submit_next() -> None:
            if stop:
                return
            while True:
                job = next(pending, None)
                if job is None:
                    return
                claim = start_attempt(db, run, job)
                if claim is not None:
                    break
                counts["skipped_claimed"] += 1
            attempt_id, raw_path = claim
            counts["started"] += 1
            active[pool.submit(fetch_and_store, job, auth, raw_path, timeout)] = (attempt_id, job)

        for _ in range(min(workers, len(queue))):
            submit_next()
        while active:
            done, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in done:
                attempt_id, job = active.pop(future)
                try:
                    state = finalize(db, run, job, attempt_id, future.result(), auth)
                except StopBatch as error:
                    stop, state = str(error), "error"
                except (OSError, ValueError, KeyError) as error:
                    state = "inflight"
                    print(json.dumps({"job_key": job["job_key"], "finalize_error": type(error).__name__}), flush=True)
                counts[state] += 1
                print(json.dumps({"job_key": job["job_key"], "query": job["params"].get("query"),
                                  "engine": job["engine"], "status": state}, ensure_ascii=False), flush=True)
                if state == "error" and (job_last_code(db, job) == "110"):
                    time.sleep(30)
                submit_next()
    counts["stopped"] = stop
    return counts


def job_last_code(db: sqlite3.Connection, job: dict) -> str | None:
    row = db.execute("SELECT last_error_code FROM jobs WHERE job_key=?", (job["job_key"],)).fetchone()
    return row[0] if row else None


def inflight_rows(db: sqlite3.Connection, jobs_by_key: dict) -> list[dict]:
    rows = db.execute("""SELECT a.attempt_id,a.job_key,a.started_utc,a.raw_file FROM attempts a
        JOIN jobs j ON j.job_key=a.job_key WHERE j.status='inflight' AND a.finished_utc IS NULL""")
    return [{"attempt_id": a, "job_key": k, "query": jobs_by_key.get(k, {}).get("params", {}).get("query"),
             "started_utc": s, "raw_file": r} for a, k, s, r in rows if k in jobs_by_key]


# ---------- экспорт ----------

def write_tsv(path: Path, fields: list[str], rows: list[dict]) -> None:
    fd, temp = tempfile.mkstemp(prefix=".export-", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, path)


def host(url: str) -> str:
    try:
        name = urllib.parse.urlparse(url if "://" in url else "https://" + url).hostname or ""
    except ValueError:
        return ""
    return name.removeprefix("www.")


def clean_text(value: str) -> str:
    return re.sub(r"</?b>", "", urllib.parse.unquote(value or ""))


def success_payloads(db: sqlite3.Connection, run: Path, jobs: list[dict]):
    attempts = dict(db.execute("""SELECT j.job_key, a.raw_file || '|' || a.raw_sha256 || '|' || a.started_utc
        FROM jobs j JOIN attempts a ON a.attempt_id=j.success_attempt WHERE j.status='success'"""))
    for job in jobs:
        if job["job_key"] not in attempts:
            continue
        rel, digest, when = attempts[job["job_key"]].split("|", 2)
        body = (run / rel).read_bytes()
        if sha256(body) != digest:
            raise ValueError(f"Контрольная сумма сырого ответа не совпала: {rel}")
        yield job, parse_response(job["kind"], body, 200, job["params"].get("pagetype")), rel, digest, when


def export_serp(db: sqlite3.Connection, run: Path, jobs: list[dict]) -> dict:
    organic, features, ads = [], [], []
    page_docs: dict[tuple, list] = {}
    for job, parsed, rel, digest, when in success_payloads(db, run, jobs):
        row = job["row"]
        series = json.dumps({k: v for k, v in job["params"].items() if k != "page"}, sort_keys=True)
        common = {**row, "page": job["page"], "doc_rank": 1, "_series": series, "collected_at": when, "raw_json_path": "",
                  "raw_xml_path": rel, "raw_html_path": rel, "provider": "xmlriver", "engine": job["engine"],
                  "device": job["params"]["device"], "job_key": job["job_key"], "raw_sha256": digest,
                  "corrected_query": parsed.get("corrected", "")}
        urls = []
        for rank, doc in enumerate(parsed["organic"], start=1):
            url = (doc.findtext("url") or "").strip()
            urls.append(url)
            title = (doc.findtext("title") or "").strip()
            passage = " ".join((p.text or "").strip() for p in doc.findall("./passages/passage"))
            organic.append({**common, "group_rank": rank, "result_rank": rank, "result_title": title,
                            "result_headline": passage, "result_title_or_snippet": title or passage,
                            "result_domain": host(url), "source_url": url, "contenttype": "organic"})
        page_docs[(job["engine"], series, job["page"])] = (urls, parsed.get("corrected", ""), len(parsed["features"]))
        for rank, doc in enumerate(parsed["features"], start=1):
            url = (doc.findtext("url") or "").strip()
            features.append({**common, "group_rank": rank, "result_rank": rank, "result_domain": host(url),
                             "source_url": url, "result_title": (doc.findtext("title") or "").strip(),
                             "contenttype": (doc.findtext("contenttype") or "").strip()})
        for position, (block, node) in enumerate(parsed["ads"], start=1):
            url, adsurl = (node.findtext("url") or "").strip(), (node.findtext("adsurl") or "").strip()
            title, snippet = (node.findtext("title") or "").strip(), (node.findtext("snippet") or "").strip()
            sitelinks = [(s.findtext("title") or "").strip() for s in node.findall(".//sitelink")]
            ads.append({**common, "group_rank": position, "result_rank": position, "serp_position": block,
                        "ad_position": position, "result_title": title, "result_headline": snippet,
                        "result_title_or_snippet": title or snippet,
                        "result_domain": "" if host(url).startswith("yabs.") else host(url),
                        "source_url": url, "count_url": adsurl or (url if block == "rightads" else ""),
                        "block": block, "adsurl": adsurl, "title_clean": clean_text(title),
                        "snippet_clean": clean_text(snippet), "sitelinks_json": json.dumps(sitelinks, ensure_ascii=False),
                        "landing_status": "landing-unresolved", "landing_url": ""})
    for row in organic:
        row["abs_rank_state"] = rank_state(page_docs, row)
    engines = sorted({j["engine"] for j in jobs})
    written = []
    for name, fields, rows in (("serp_results", RESULT_HEADER + SERP_EXTRA, organic),
                               ("feature_rows", RESULT_HEADER + SERP_EXTRA, features),
                               ("ad_rows", AD_RESULT_HEADER + AD_EXTRA, ads)):
        # Прежние потребители группируют только по запросу и региону: две системы в одной таблице
        # смешались бы, поэтому общая таблица пишется только для одной системы, иначе — по файлу на систему.
        for stale in [run / f"{name}.tsv", *(run / f"{name}_{e}.tsv" for e in ("yandex", "google"))]:
            if stale.exists():
                stale.unlink()
        if len(engines) == 1:
            write_tsv(run / f"{name}.tsv", fields, rows)
            written.append(f"{name}.tsv")
        else:
            for engine in engines:
                write_tsv(run / f"{name}_{engine}.tsv", fields, [r for r in rows if r["engine"] == engine])
                written.append(f"{name}_{engine}.tsv")
    return {"organic_rows": len(organic), "feature_rows": len(features), "ad_rows": len(ads), "files": written}


def rank_state(page_docs: dict, row: dict) -> str:
    """Абсолютная позиция доказана только непрерывной цепочкой страниц без пересечений адресов."""
    page = int(row["page"])
    if page == 0:
        return "verified"
    if row["engine"] == "google":
        return "not_verified_google"
    key = [(row["engine"], row["_series"], page)]
    if key[0] not in page_docs:
        return "unknown"
    seen: set[str] = set()
    for previous in range(page + 1):
        docs = page_docs.get((row["engine"], row["_series"], previous))
        if docs is None:
            return "previous_page_missing_or_not_successful"
        urls, corrected, features = docs
        if previous < page and (len(urls) != 10 or features):
            return "previous_page_incomplete"
        if corrected != page_docs[key[0]][1]:
            return "corrected_query_changed"
        if seen & set(urls):
            return "url_overlap_between_pages"
        seen |= set(urls)
    return "verified"


def wordstat_number(value) -> int:
    text = str(value).replace(" ", "").replace(" ", "")
    if not text.isdigit():
        raise ValueError(f"не число: {value!r}")
    return int(text)


def finite_share(value) -> float:
    share = float(str(value).replace(",", "."))
    if not math.isfinite(share) or share < 0:
        raise ValueError(f"доля не конечное неотрицательное число: {value!r}")
    return share


def export_wordstat(db: sqlite3.Connection, run: Path, jobs: list[dict]) -> dict:
    bundle = run / "raw_bundle"
    bundle.mkdir(mode=0o700, exist_ok=True)
    # Повторный экспорт пересобирает каталог целиком: прежние файлы иначе попали бы в рендер дважды.
    for stale in [*bundle.glob("top_requests_*.json"), *bundle.glob("dynamics_*.json"), *bundle.glob("_manifest.json"),
                  *bundle.glob("region_*/top_requests_*.json"), *bundle.glob("region_*/dynamics_*.json"),
                  *bundle.glob("region_*/_manifest.json")]:
        stale.unlink()
    grouped: dict[tuple, dict] = {}
    row_errors = []
    for job, parsed, rel, digest, _ in success_payloads(db, run, jobs):
        key = (job["row"]["mask"], job["row"]["region"])
        item = grouped.setdefault(key, {"provider": "xmlriver", "requestPhrase": job["row"]["mask"],
                                         "regions": job["row"]["region"], "devices": job["row"]["devices"],
                                         "raw_files": [], "raw_sha256": []})
        item["raw_files"].append(rel)
        item["raw_sha256"].append(digest)
        data = parsed["data"]
        if job["row"]["pagetype"] == "words":
            for field, target in (("popular", "results"), ("associations", "associations")):
                rows = []
                for entry in data.get(field) or []:
                    raw = str(entry.get("text", ""))
                    try:
                        rows.append({"phrase": re.sub(r"\s+", " ", re.sub(r"(?<!\S)\+(?=\S)", "", raw)).strip(),
                                     "count": wordstat_number(entry.get("value")), "phrase_raw": raw})
                    except ValueError as error:
                        row_errors.append({"mask": key[0], "region": key[1], "field": field, "text": raw,
                                           "error": str(error)})
                item[target] = rows
        else:
            graph = data.get("graph") or {}
            series = (((graph.get("images") or {}).get("timeSeries") or {}).get("rawValues")) or graph.get("tableData") or []
            points = []
            for point in series:
                try:
                    points.append({"date": datetime.fromtimestamp(int(point["startTimestamp"]) / 1000, MSK).date().isoformat(),
                                   "count": wordstat_number(point.get("absoluteValue")),
                                   "share": finite_share(point.get("value", "0"))})
                except (KeyError, TypeError, ValueError, OverflowError, OSError) as error:
                    row_errors.append({"mask": key[0], "region": key[1], "field": "graph", "text": json.dumps(point, ensure_ascii=False)[:200],
                                       "error": f"{type(error).__name__}: {error}"})
            item["dynamics"] = points
            if data.get("totalValue") is not None:
                try:
                    item["totalCount"] = wordstat_number(data["totalValue"])
                    item["totalCountSource"] = "xmlriver_history_totalValue_previous_month"
                except ValueError as error:
                    row_errors.append({"mask": key[0], "region": key[1], "field": "totalValue",
                                       "text": str(data["totalValue"])[:200], "error": str(error)})
    # Один регион — файлы прямо в raw_bundle (как у облачного сборщика); несколько — по каталогу на регион,
    # чтобы рендер волны не смешивал регионы.
    regions = sorted({r for (_, r) in grouped})
    manifests: dict[Path, list] = {}
    for (mask, region), item in grouped.items():
        target = bundle if len(regions) == 1 else bundle / f"region_{region or 'all'}"
        target.mkdir(mode=0o700, exist_ok=True)
        readable = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ_-]+", "_", mask).lower()[:55].strip("_") or "mask"
        stub = f"{readable}_{sha256(mask.encode('utf-8'))[:10]}"
        bad = [e for e in row_errors if e["mask"] == mask and e["region"] == region]
        for artifact, present in (("top_requests", "results" in item), ("dynamics", "dynamics" in item)):
            if not present:
                continue
            path = target / f"{artifact}_{stub}.json"
            skip = ("dynamics",) if artifact == "top_requests" else ("results", "associations")
            payload = {k: v for k, v in item.items() if k not in skip}
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
            manifests.setdefault(target, []).append(
                {"mask": mask, "source_mask": mask, "artifact": artifact, "type": artifact,
                 "status": "partial" if bad else "success", "row_errors": len(bad), "file": str(path),
                 "provider": "xmlriver", "regions": region})
    for target, entries in manifests.items():
        (target / "_manifest.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    errors_file = run / "wordstat_row_errors.tsv"
    if errors_file.exists():
        errors_file.unlink()
    if row_errors:
        write_tsv(errors_file, ["mask", "region", "field", "text", "error"], row_errors)
    return {"artifacts": sum(len(e) for e in manifests.values()), "row_errors": len(row_errors),
            "complete": not row_errors, "region_dirs": len(regions) > 1}


# ---------- команды ----------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("info", "plan", "collect", "export", "inflight"))
    parser.add_argument("--kind", choices=("serp", "wordstat"), default="serp")
    parser.add_argument("--output-dir", "--run-dir", dest="output_dir", default="xmlriver-run")
    parser.add_argument("--credentials-file", help="закрытый файл 0600: KEY=VALUE или JSON {user,key}")
    parser.add_argument("--use-demo-key", action="store_true",
                        help="общий демо-доступ из config/ для короткой пробы (потолок 2 руб. за запуск)")
    parser.add_argument("--jobs-file", help="TSV заданий выдачи: job_id, search_query, region_id[, page, engine, ...]")
    parser.add_argument("--engine", choices=("yandex", "google", "both"), default="yandex")
    parser.add_argument("--device", choices=("desktop", "tablet", "mobile"), default="desktop")
    parser.add_argument("--pages", type=int, default=1, help="страниц на запрос, если в TSV нет колонки page")
    parser.add_argument("--ads", choices=("on", "off"), default="off")
    parser.add_argument("--yandex-right-ads", action="store_true")
    parser.add_argument("--google-country", default="2643")
    parser.add_argument("--google-lang", default="ru")
    parser.add_argument("--google-loc", default="")
    parser.add_argument("--google-domain", default="")
    parser.add_argument("--ai", action="store_true", help="платный разбор блока ИИ (ai=1)")
    parser.add_argument("--ai-price-per-1000", help="надбавка за ai=1 в руб. за 1000 запросов по вашему тарифу; "
                                                    "обязательна для collect с --ai")
    parser.add_argument("--masks-file", help="маски Wordstat: по одной в строке или TSV с колонкой mask")
    parser.add_argument("--regions", default="225", help="регионы Яндекса через запятую, по заданию на регион")
    parser.add_argument("--devices", default="all", help="all или desktop,phone,tablet")
    parser.add_argument("--pagetypes", default="words,history")
    parser.add_argument("--period", choices=("month", "week", "day"), default="month")
    parser.add_argument("--start", help="dd.mm.yyyy для history")
    parser.add_argument("--end", help="dd.mm.yyyy для history")
    parser.add_argument("--price-per-1000", default="25", help="ориентир цены для plan без сети")
    parser.add_argument("--approve-plan-sha256")
    parser.add_argument("--max-cost-rub")
    parser.add_argument("--max-new", type=int)
    parser.add_argument("--probe", type=int, help="выполнить первые N заданий и остановиться")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument("--only-codes", default="101,110,111,500")
    parser.add_argument("--request-timeout", type=int, default=120)
    parser.add_argument("--job-key", help="для inflight: снять одно задание")
    parser.add_argument("--acknowledge-possible-charge", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        return run_command(build_parser().parse_args(argv))
    finally:
        while OPEN_DBS:
            OPEN_DBS.pop().close()


def run_command(args: argparse.Namespace) -> int:
    run = Path(args.output_dir).expanduser().resolve()
    if args.command == "info":
        auth, demo = credentials(args)
        info = get_info(auth)
        print(json.dumps({k: info.get(k) for k in ("balance", "cost", "threads", "engine", "tarif")}
                         | {"demo_key": demo}, ensure_ascii=False, indent=1))
        return 0
    if args.kind == "serp" and not args.jobs_file:
        raise ValueError("Для --kind serp нужен --jobs-file.")
    if args.kind == "wordstat" and not args.masks_file:
        raise ValueError("Для --kind wordstat нужен --masks-file.")
    jobs = serp_jobs(args) if args.kind == "serp" else wordstat_jobs(args)
    by_key = {j["job_key"]: j for j in jobs}
    plan = plan_sha(args.kind, jobs)
    db = open_db(run, create=args.command == "collect")
    state = statuses(db, jobs)
    counts = {s: list(state.values()).count(s) for s in ("pending", "inflight", "success", "empty", "error")}
    if args.command == "plan":
        price = Decimal(args.price_per_1000) / 1000 + (ai_extra_per_request(args) if args.ai and args.ai_price_per_1000
                                                        and args.kind == "serp" else Decimal(0))
        todo = counts["pending"] + counts["error"]
        print(json.dumps({"jobs_total": len(jobs), "by_engine": {e: sum(j["engine"] == e for j in jobs)
                                                                  for e in sorted({j["engine"] for j in jobs})},
                          "status": counts, "estimate_rub_for_remaining": str(price * todo),
                          "price_note": f"ориентир {args.price_per_1000} руб./1000; точную цену collect берёт из get_info",
                          "plan_sha256": plan,
                          "warnings": [w for w in (
                              "Google через XMLRiver рекламу в проверках автора не возвращал — сначала одиночная проба."
                              if args.kind == "serp" and args.ads == "on" and any(j["engine"] == "google" for j in jobs) else "",
                              "ai=1 — платная надбавка, проверьте пробой." if args.ai else "",
                              "Больше 20 заданий: начните с --probe 3." if len(jobs) > 20 else "") if w]},
                         ensure_ascii=False, indent=1))
        return 0
    if db is None:
        raise ValueError("Журнала ещё нет: сначала plan и collect.")
    if args.command == "export":
        result = export_serp(db, run, jobs) if args.kind == "serp" else export_wordstat(db, run, jobs)
        # Полнота — по всему плану: невыполненные, ошибочные и зависшие задания делают экспорт неполным.
        unfinished = counts["pending"] + counts["error"] + counts["inflight"]
        result["complete"] = not result.get("row_errors") and unfinished == 0
        result["unfinished_jobs"] = unfinished
        print(json.dumps({**result, "status": counts}, ensure_ascii=False))
        return 0 if result["complete"] else 2
    if args.command == "inflight":
        rows = inflight_rows(db, by_key)
        if not args.job_key:
            print(json.dumps({"inflight": rows}, ensure_ascii=False, indent=1))
            return 0
        if not args.acknowledge_possible_charge:
            raise ValueError("Снятие задания с неизвестным исходом требует --acknowledge-possible-charge: запрос мог быть оплачен.")
        with db:
            db.execute("UPDATE attempts SET finished_utc=?,failure_class='manual_unknown_outcome' "
                       "WHERE job_key=? AND finished_utc IS NULL", (utc_now(), args.job_key))
            db.execute("UPDATE jobs SET status='pending' WHERE job_key=? AND status='inflight'", (args.job_key,))
        print(json.dumps({"job_key": args.job_key, "status": "pending"}))
        return 0
    if args.approve_plan_sha256 != plan:
        raise ValueError(f"collect требует --approve-plan-sha256 из plan (сейчас план {plan}).")
    if not args.max_cost_rub:
        raise ValueError("collect требует --max-cost-rub.")
    cap = Decimal(args.max_cost_rub)
    auth, demo = credentials(args)
    if demo and cap > DEMO_MAX_COST:
        raise ValueError(f"С демо-доступом потолок не больше {DEMO_MAX_COST} руб. за запуск: заведите свой ключ XMLRiver.")
    if args.ai and demo:
        raise ValueError("Платный режим --ai с демо-доступом запрещён: заведите свой ключ XMLRiver.")
    ai_extra = ai_extra_per_request(args)
    with db:
        for job in jobs:
            db.execute("INSERT OR IGNORE INTO jobs(job_key,kind,engine,spec_json,status) VALUES(?,?,?,?,'pending')",
                       (job["job_key"], job["kind"], job["engine"], json.dumps(job["params"], ensure_ascii=False)))
    lock = open(run / ".collect.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise ValueError("В этом каталоге уже идёт другой collect: два процесса могли бы оплатить один запрос дважды.") from None
    recovered = recover_saved(db, run, by_key, auth)
    state = statuses(db, jobs)
    retry_codes = set(args.only_codes.split(","))
    queue = [j for j in jobs if state[j["job_key"]] == "pending" or
             (args.retry_errors and state[j["job_key"]] == "error" and job_last_code(db, j) in retry_codes)]
    limit = args.probe or args.max_new
    queue = queue[:limit] if limit else queue
    if not queue:
        print(json.dumps({"new_requests": 0, "recovered": recovered, "status": counts}, ensure_ascii=False))
        return 0
    info = get_info(auth)
    costs, threads = info.get("cost") or {}, info.get("threads") or {}
    for engine in {j["engine"] for j in queue}:
        if (info.get("engine") or {}).get(engine) != 1 or engine not in costs:
            raise ValueError(f"Система {engine} недоступна в XMLRiver или нет её цены.")
    estimate = sum(Decimal(str(costs[j["engine"]])) / 1000 + (ai_extra if j["kind"] == "serp" else 0) for j in queue)
    if estimate > cap or estimate > Decimal(str(info.get("balance", 0))):
        raise ValueError(f"Оценка {estimate} руб. больше потолка {cap} или баланса {info.get('balance')}.")
    workers = max(1, min(args.workers, min(int(threads.get(j["engine"], 3)) for j in queue) - 2))
    result = collect(db, run, queue, auth, workers, max(60, args.request_timeout))
    try:
        balance_after = get_info(auth).get("balance")
    except ValueError:
        balance_after = None
    print(json.dumps({"new_requests": result["started"], "queued": len(queue), **result, "recovered": recovered, "estimate_rub": str(estimate),
                      "balance_before": info.get("balance"), "balance_after": balance_after,
                      "balance_note": "разница общего баланса может включать чужие запросы", "demo_key": demo},
                     ensure_ascii=False, indent=1))
    if result["stopped"]:
        return 3
    return 0 if not result["error"] and not result["inflight"] else 2


if __name__ == "__main__":
    os.umask(0o077)
    try:
        sys.exit(main())
    except (ValueError, FileNotFoundError, sqlite3.Error) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)
