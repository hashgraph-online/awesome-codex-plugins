#!/usr/bin/env python3
"""Scrape.ly helper for coding assistants (Claude Code, Cursor, Codex).

Find a Store Actor for a scraping task, run it, and read its results, with
output kept small enough for an LLM context. Standard library only.

    scrapely_agent.py search "google maps restaurants" [--limit 5]
    scrapely_agent.py details compass/crawler-google-places
    scrapely_agent.py run compass/crawler-google-places --input '{"searchStringsArray":["pizza"]}' [--max-items 20]
    scrapely_agent.py status <runId>
    scrapely_agent.py output <runId or datasetId> [--limit 20] [--offset 0] [--fields title,url]
    scrapely_agent.py record <runId> [--key OUTPUT]

Environment:
    SCRAPELY_TOKEN     your API token (required for run/status/output/record)
    SCRAPELY_API_URL   API base URL (default https://api.scrape.ly)

Every command prints one JSON object on stdout. Errors print
{"error": {...}} and exit with status 1. The token is never printed.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

VERSION = "0.1.0"
DEFAULT_API_URL = "https://api.scrape.ly"
TERMINAL = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT", "TIMED_OUT"}
MAX_STRING = 400
MAX_OUTPUT_CHARS = 24_000
MAX_FIELDS = 60
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_ERROR_BYTES = 64 * 1024


class ApiError(Exception):
    def __init__(self, status: int, type_: str, message: str):
        super().__init__(message)
        self.status = status
        self.type = type_
        self.message = message


def api_url() -> str:
    return (os.environ.get("SCRAPELY_API_URL") or os.environ.get("SCRAPELY_API_BASE_URL") or DEFAULT_API_URL).rstrip("/")


def token(required: bool) -> str | None:
    value = (os.environ.get("SCRAPELY_TOKEN") or "").strip()
    if required and not value:
        raise ApiError(0, "missing-token", "Set SCRAPELY_TOKEN to your Scrape.ly API token (Console > Settings > API & Integrations).")
    return value or None


def request(method: str, path: str, *, params: dict | None = None, body: Any = None, auth: bool = True, timeout: float = 90,
            headers_extra: dict | None = None, retries: int | None = None) -> Any:
    """One API call. GETs (and POSTs that carry an Idempotency-Key) are retried on network errors."""
    safe = method == "GET" or bool(headers_extra and headers_extra.get("Idempotency-Key"))
    attempts = 1 + (retries if retries is not None else (3 if safe else 0))
    for attempt in range(attempts):
        try:
            return _request_once(method, path, params=params, body=body, auth=auth, timeout=timeout, headers_extra=headers_extra)
        except ApiError as exc:
            retryable = exc.type == "network-error" or exc.status in (502, 503, 504)
            if not retryable or attempt == attempts - 1:
                raise
            time.sleep(min(2 ** attempt, 8))
    raise AssertionError("unreachable")


def _request_once(method: str, path: str, *, params: dict | None, body: Any, auth: bool, timeout: float, headers_extra: dict | None) -> Any:
    url = api_url() + path
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    headers = {"Accept": "application/json", "User-Agent": f"scrapely-agent-skill/{VERSION}"}
    headers.update(headers_extra or {})
    tok = token(required=auth)
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ApiError(0, "response-too-large", f"The API response is larger than {MAX_RESPONSE_BYTES} bytes.")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_ERROR_BYTES).decode(errors="replace")
        exc.close()
        try:
            err = json.loads(raw).get("error") or {}
        except (ValueError, AttributeError):
            err = {}
        raise ApiError(exc.code, str(err.get("type") or "http-error"), str(err.get("message") or raw[:300] or exc.reason)) from None
    except urllib.error.URLError as exc:
        raise ApiError(0, "network-error", str(exc.reason)) from None
    except (http.client.HTTPException, OSError) as exc:  # dropped connection, timeout
        raise ApiError(0, "network-error", f"{type(exc).__name__}: {exc}") from None


def actor_path_id(actor: str) -> str:
    """'user/name' or 'user~name' or an Actor ID -> path segment."""
    return urllib.parse.quote(actor.strip().replace("/", "~"), safe="~")


def clip(value: Any, max_len: int = MAX_STRING) -> Any:
    if isinstance(value, str):
        return value if len(value) <= max_len else value[: max_len - 1] + "…"
    if isinstance(value, list):
        return [clip(v, max_len) for v in value]
    if isinstance(value, dict):
        return {k: clip(v, max_len) for k, v in value.items()}
    return value


def bound(value: Any, max_len: int = MAX_STRING, max_entries: int = MAX_FIELDS) -> Any:
    """clip() that also keeps at most `max_entries` entries of every list and object (keys clipped too)."""
    if isinstance(value, list):
        return [bound(v, max_len, max_entries) for v in value[:max_entries]]
    if isinstance(value, dict):
        return {clip(str(k), max_len): bound(v, max_len, max_entries) for k, v in list(value.items())[:max_entries]}
    return clip(value, max_len)


def json_size(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False))


def squeeze(value: Any, budget: int) -> Any:
    """bound() a value; if its JSON is still over `budget` characters, a clipped JSON string of it instead."""
    value = bound(value)
    if json_size(value) <= budget:
        return value
    text, cut = json.dumps(value, ensure_ascii=False), budget
    while cut > 1 and json_size(clip(text, cut)) > budget:
        cut //= 2
    return clip(text, cut)


def fit_items(items: list, budget: int = MAX_OUTPUT_CHARS, clipped: bool = False) -> tuple[list, bool]:
    """Clip long strings (unless `clipped`: already squeezed), then keep as many whole items as fit the character budget."""
    out, used = [], 0
    for item in items:
        c = item if clipped else clip(item)
        size = json_size(c)
        if out and used + size > budget:
            return out, True
        out.append(c)
        used += size
    return out, False


# ── commands ────────────────────────────────────────────────────────────────


def cmd_search(args: argparse.Namespace) -> dict:
    data = request("GET", "/v2/store", params={"responseFormat": "agent", "search": args.query, "limit": args.limit, "offset": args.offset}, auth=False)["data"]
    items = []
    for it in data.get("items", []):
        if "actor" not in it:  # server without the agent format: compact the full entry
            it = {
                "actor": f"{it.get('username')}/{it.get('name')}",
                "title": it.get("title"),
                "purpose": clip(it.get("description") or "", 160),
                "pricing": {"model": (it.get("currentPricingInfo") or {}).get("pricingModel", "FREE")},
                "rating": {"average": it.get("avgRating"), "count": it.get("totalReviews")},
                "health": "under-maintenance" if it.get("isUnderMaintenance") else "ok",
            }
        items.append({
            k: squeeze(it.get(k), 1500)
            for k in ("actor", "title", "purpose", "inputs", "inputExample", "outputFields", "pricing", "rating", "health", "notice", "stats")
            if it.get(k) not in (None, [], {})
        })
    out: dict[str, Any] = {"total": data.get("total"), "offset": data.get("offset"),
                           "next": "Pick the best match (health ok, most users, fitting price), then write the input JSON to a file with your file-editing tool (never inline it in a shell command) and run: run <actor> --input @<file>"}
    shown, truncated = fit_items(items, MAX_OUTPUT_CHARS - json_size(out) - 100, clipped=True)
    out |= {"count": len(shown), "items": shown}
    if truncated:
        out["nextOffset"] = args.offset + len(shown)
    return out


def cmd_details(args: argparse.Namespace) -> dict:
    actor = request("GET", f"/v2/acts/{actor_path_id(args.actor)}", auth=bool(token(False)))["data"]
    definition = actor.get("defaultBuildActorDefinition") or {}
    schema = definition.get("inputSchema") if isinstance(definition.get("inputSchema"), dict) else definition.get("input")
    props = (schema or {}).get("properties") or {} if isinstance(schema, dict) else {}
    required = set((schema or {}).get("required") or []) if isinstance(schema, dict) else set()
    fields = []
    for name, p in props.items():
        if not isinstance(p, dict) or p.get("editor") == "hidden":
            continue
        f = {"name": clip(str(name), 120), "type": squeeze(p.get("type"), 120), "required": name in required}
        if p.get("description") or p.get("title"):
            f["description"] = clip(str(p.get("description") or p.get("title")), 200)
        if "enum" in p and not p.get("isSecret"):
            # Every allowed value (only long ones clipped): a cut list would hide valid choices.
            f["enum"] = clip(p["enum"], 120)
        for key in ("default", "prefill"):
            if key in p and not p.get("isSecret"):
                f[key] = squeeze(p[key], 1000)
        fields.append(f)
    example = (actor.get("exampleRunInput") or {}).get("body")
    try:
        example = json.loads(example) if isinstance(example, str) else example
    except ValueError:
        example = None
    out: dict[str, Any] = {
        "actor": clip(f"{actor.get('username')}/{actor.get('name')}", 200),
        "title": clip(actor.get("title"), 200),
        "description": clip(actor.get("description") or "", 500),
        "isUnderMaintenance": bool(actor.get("isUnderMaintenance")),
        "pricingInfos": squeeze((actor.get("pricingInfos") or [])[:1] if isinstance(actor.get("pricingInfos"), list) else [], 3000),
        "exampleInput": squeeze(example, 6000),
    }
    # The rest of the output budget goes to the input fields: required ones
    # first, then the others, each group in schema order.
    fields = [f for f in fields if f["required"]] + [f for f in fields if not f["required"]]
    shown, _ = fit_items(fields[:MAX_FIELDS], MAX_OUTPUT_CHARS - json_size(out) - 100, clipped=True)
    out["inputFields"] = shown
    if len(shown) < len(fields):
        out["moreInputFields"] = len(fields) - len(shown)
    return out


def _run_summary(run: dict) -> dict:
    return {k: run.get(k) for k in ("id", "status", "statusMessage", "startedAt", "finishedAt", "defaultDatasetId", "defaultKeyValueStoreId") if run.get(k) is not None} | (
        {"usageTotalUsd": run.get("usageTotalUsd")} if run.get("usageTotalUsd") is not None else {}
    )


def cmd_run(args: argparse.Namespace) -> dict:
    raw = args.input
    if raw.startswith("@"):
        # Only a .json file inside the working directory, so a misled agent cannot send other local files as input
        cwd = os.path.realpath(os.getcwd())
        path = os.path.realpath(raw[1:])
        if os.path.commonpath([cwd, path]) != cwd or not path.endswith(".json") or not os.path.isfile(path):
            raise ApiError(0, "invalid-input", "--input @file must be a .json file inside the current directory")
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    try:
        run_input = json.loads(raw)
    except ValueError as exc:
        raise ApiError(0, "invalid-input", f"--input is not valid JSON: {exc}") from None
    params: dict[str, Any] = {}
    if args.max_items:
        params["maxItems"] = args.max_items
    if args.max_charge_usd:
        params["maxTotalChargeUsd"] = args.max_charge_usd
    # Start without waiting, so the call returns at once; a retry after a dropped
    # connection reuses the Idempotency-Key and gets the same run, never a second one.
    run = request("POST", f"/v2/acts/{actor_path_id(args.actor)}/runs", params=params, body=run_input,
                  headers_extra={"Idempotency-Key": f"agent-{uuid.uuid4().hex}"}, retries=3)["data"]
    deadline = time.time() + args.wait
    while run.get("status") not in TERMINAL and time.time() < deadline:
        wait = min(30, max(1, int(deadline - time.time())))
        run = request("GET", f"/v2/actor-runs/{run['id']}", params={"waitForFinish": wait}, timeout=wait + 30)["data"]
    result: dict[str, Any] = {"run": _run_summary(run)}
    if run.get("status") not in TERMINAL:
        result["next"] = f"Still {run.get('status')}. Check later with: status {run['id']}, then: output {run['id']}"
        return result
    if run.get("defaultDatasetId"):
        result["output"] = _items(run["defaultDatasetId"], 0, args.limit, None)
    if run.get("status") != "SUCCEEDED":
        result["next"] = "The run did not succeed. Read statusMessage, fix the input, or try another Actor from search."
    return result


def cmd_status(args: argparse.Namespace) -> dict:
    return {"run": _run_summary(request("GET", f"/v2/actor-runs/{args.run_id}")["data"])}


def _items(dataset_id: str, offset: int, limit: int, fields: str | None) -> dict:
    params = {"offset": offset, "limit": limit, "clean": "true", "fields": fields}
    url_path = f"/v2/datasets/{urllib.parse.quote(dataset_id)}/items"
    items = request("GET", url_path, params=params | {"format": "json"})
    if isinstance(items, dict) and "data" in items:  # wrapped variants
        items = items["data"].get("items", items["data"]) if isinstance(items["data"], dict) else items["data"]
    items = items if isinstance(items, list) else []
    info = request("GET", f"/v2/datasets/{urllib.parse.quote(dataset_id)}")["data"]
    total = info.get("itemCount") or info.get("cleanItemCount")
    shown, truncated = fit_items(items)
    out: dict[str, Any] = {"datasetId": dataset_id, "total": total, "offset": offset, "count": len(shown), "items": shown}
    next_offset = offset + len(shown)
    if truncated or (isinstance(total, int) and next_offset < total):
        out["nextOffset"] = next_offset
        out["hint"] = f"More items: output {dataset_id} --offset {next_offset} --limit {limit}" + (" (use --fields to keep only the columns you need)" if not fields else "")
    return out


def cmd_output(args: argparse.Namespace) -> dict:
    target = args.target
    dataset_id = target
    try:
        run = request("GET", f"/v2/actor-runs/{urllib.parse.quote(target)}")["data"]
        dataset_id = run.get("defaultDatasetId") or target
    except ApiError as exc:
        if exc.status not in (404, 400):
            raise
    return _items(dataset_id, args.offset, args.limit, args.fields)


def cmd_record(args: argparse.Namespace) -> dict:
    run = request("GET", f"/v2/actor-runs/{urllib.parse.quote(args.run_id)}")["data"]
    store = run.get("defaultKeyValueStoreId")
    url = api_url() + f"/v2/key-value-stores/{store}/records/{urllib.parse.quote(args.key)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token(True)}", "User-Agent": f"scrapely-agent-skill/{VERSION}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            ctype = resp.headers.get("Content-Type", "")
            raw = resp.read(MAX_OUTPUT_CHARS + 1)
    except urllib.error.HTTPError as exc:
        exc.close()
        if exc.code == 404:
            return {"key": args.key, "found": False}
        raise ApiError(exc.code, "http-error", exc.reason) from None
    if "json" in ctype:
        try:
            return {"key": args.key, "contentType": ctype, "value": clip(json.loads(raw))}
        except ValueError:
            pass
    if ctype.startswith("text/") or "json" in ctype:
        text = raw.decode(errors="replace")
        return {"key": args.key, "contentType": ctype, "value": text[:MAX_OUTPUT_CHARS], "truncated": len(raw) > MAX_OUTPUT_CHARS}
    return {"key": args.key, "contentType": ctype, "binary": True, "url": url}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="scrapely_agent.py", description="Find, run and read Scrape.ly Store Actors.")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="find Store Actors for a task")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=5)
    s.add_argument("--offset", type=int, default=0)
    s.set_defaults(fn=cmd_search)
    s = sub.add_parser("details", help="full input fields of one Actor")
    s.add_argument("actor")
    s.set_defaults(fn=cmd_details)
    s = sub.add_parser("run", help="run an Actor and return its first results")
    s.add_argument("actor")
    s.add_argument("--input", default="{}", help="input JSON, or @file.json")
    s.add_argument("--wait", type=int, default=300, help="seconds to wait for the run (default 300)")
    s.add_argument("--max-items", type=int, default=None, help="cap on result items (pay-per-result Actors)")
    s.add_argument("--max-charge-usd", type=float, default=None, help="cap on the run's total cost")
    s.add_argument("--limit", type=int, default=20, help="items to return (default 20)")
    s.set_defaults(fn=cmd_run)
    s = sub.add_parser("status", help="state of a run")
    s.add_argument("run_id")
    s.set_defaults(fn=cmd_status)
    s = sub.add_parser("output", help="result items of a run or dataset, paged")
    s.add_argument("target", help="run ID or dataset ID")
    s.add_argument("--offset", type=int, default=0)
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--fields", default=None, help="comma-separated fields to keep")
    s.set_defaults(fn=cmd_output)
    s = sub.add_parser("record", help="a key-value store record of a run (default OUTPUT)")
    s.add_argument("run_id")
    s.add_argument("--key", default="OUTPUT")
    s.set_defaults(fn=cmd_record)
    args = p.parse_args(argv)
    try:
        result = args.fn(args)
    except ApiError as exc:
        print(json.dumps({"error": {"status": exc.status, "type": exc.type, "message": exc.message}}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
