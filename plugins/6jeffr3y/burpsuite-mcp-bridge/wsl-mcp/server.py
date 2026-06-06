from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

_NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
DEFAULT_HOST = os.environ.get("BURP_MCP_BRIDGE_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("BURP_MCP_BRIDGE_PORT", "9639"))
MCP_TRANSPORT = os.environ.get("BURP_MCP_TRANSPORT", "stdio")
MCP_SERVER_HOST = os.environ.get("BURP_MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT = int(os.environ.get("BURP_MCP_SERVER_PORT", "9640"))
MCP_SERVER_PATH = os.environ.get("BURP_MCP_SERVER_PATH", "/mcp")
PLUGIN_ROOT = Path(os.environ.get("BURP_MCP_PLUGIN_ROOT", Path(__file__).resolve().parent.parent))
ARTIFACT_ROOT = PLUGIN_ROOT / "artifacts"

mcp = FastMCP(
    "BurpSuite MCP Bridge",
    instructions=(
        "Use these tools to read and operate Burp proxy traffic from Windows Burp in WSL mirrored mode. "
        "Prefer burp_target_overview(host=...) when working one target, or burp_live_overview/burp_live_poll for incremental triage, then burp_flow_get for a decisive request/response pair. "
        "Use burp_replay_flow or burp_send_raw_request when you need AI-driven request mutation and replay. "
        "Use burp_rule_upsert to install automatic request/response rewrite rules for proxied traffic; rule action is modify, drop, or spoof."
    ),
    host=MCP_SERVER_HOST,
    port=MCP_SERVER_PORT,
    streamable_http_path=MCP_SERVER_PATH,
)


def resolve_bridge_base() -> str:
    explicit = os.environ.get("BURP_MCP_BRIDGE_URL")
    if explicit:
        return explicit.rstrip("/")
    return f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"


def _request_json(path: str, method: str = "GET", payload: dict[str, Any] | None = None, query: dict[str, Any] | None = None) -> Any:
    url = resolve_bridge_base() + path
    if query:
        filtered = {k: v for k, v in query.items() if v is not None}
        if filtered:
            url += "?" + urllib.parse.urlencode(filtered)

    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with _NO_PROXY_OPENER.open(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(response_body)
            error = parsed.get("error") if isinstance(parsed, dict) else None
            if isinstance(error, dict):
                detail = f"{error.get('code', 'error')}: {error.get('message', response_body)}"
            else:
                detail = parsed.get("message", response_body) if isinstance(parsed, dict) else response_body
        except Exception:
            detail = response_body
        raise RuntimeError(f"bridge HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "无法连接 Burp MCP Bridge。请确认：1) Windows Burp 已加载扩展；2) Burp 扩展已启用；"
            f"3) WSL mirrored 下可访问 {resolve_bridge_base()}/health。底层错误：{exc.reason}"
        ) from exc

    if isinstance(data, dict) and data.get("ok") is False:
        error = data.get("error")
        if isinstance(error, dict):
            raise RuntimeError(f"{error.get('code', 'error')}: {error.get('message', 'bridge returned failure')}")
        raise RuntimeError(data.get("message") or error or "bridge returned failure")
    return data


def _timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


_STATIC_PATH_RE = re.compile(r"(?i)\.(?:css|js|mjs|map|png|jpe?g|gif|svg|ico|woff2?|ttf|eot|mp4|webm|mp3|wav|pdf|zip|gz|br|wasm)(?:$|[?#])")
_UUID_RE = re.compile(r"(?i)^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_HEX_ID_RE = re.compile(r"(?i)^[0-9a-f]{16,}$")
_LONG_TOKEN_RE = re.compile(r"(?i)^[a-z0-9_-]{24,}$")
_TARGET_SOURCE_ORDER = ("history", "live", "logger", "selection")


def _parse_source_csv(sources: str | None, default: tuple[str, ...] = _TARGET_SOURCE_ORDER) -> list[str]:
    if not sources:
        return list(default)
    requested = [part.strip().lower() for part in sources.split(",") if part.strip()]
    if not requested or "all" in requested:
        return list(default)
    allowed = set(default)
    unknown = [source for source in requested if source not in allowed]
    if unknown:
        raise ValueError(f"sources 只支持 {', '.join(default)} 或 all；未知值：{', '.join(unknown)}")
    return [source for source in default if source in requested]


def _path_no_query(path: Any) -> str:
    value = str(path or "")
    if not value:
        return "<unknown>"
    return value.split("?", 1)[0] or "/"


def _is_static_path(path: Any) -> bool:
    return bool(path and _STATIC_PATH_RE.search(str(path)))


def _normalize_endpoint_path(path: Any) -> str:
    raw = _path_no_query(path)
    if raw in {"", "<unknown>"}:
        return "<unknown>"
    leading = raw.startswith("/")
    parts = [part for part in raw.split("/") if part]
    normalized: list[str] = []
    for part in parts:
        lower = part.lower()
        if part.isdigit():
            normalized.append("{int}")
        elif _UUID_RE.match(part):
            normalized.append("{uuid}")
        elif _HEX_ID_RE.match(part):
            normalized.append("{hex}")
        elif _LONG_TOKEN_RE.match(part) and any(ch.isdigit() for ch in part) and not any(ch in lower for ch in (".", "-")):
            normalized.append("{id}")
        else:
            normalized.append(part)
    if not normalized:
        return "/"
    return ("/" if leading else "") + "/".join(normalized)


def _counter_key(value: Any, default: str = "<unknown>") -> str:
    if value is None:
        return default
    text = str(value)
    return text if text else default


def _flow_card(item: dict[str, Any], source: str | None = None, reasons: list[str] | None = None, score: int | None = None) -> dict[str, Any]:
    actual_source = source or item.get("source") or "unknown"
    flow_id = item.get("flowId")
    if flow_id is None:
        flow_id = item.get("historyId")
    card = {
        "source": actual_source,
        "flowId": flow_id,
        "method": item.get("method"),
        "host": item.get("host"),
        "path": item.get("path"),
        "endpoint": _normalize_endpoint_path(item.get("path")),
        "statusCode": item.get("statusCode"),
        "mimeType": item.get("mimeType"),
        "toolType": item.get("toolType"),
        "tags": item.get("tags") or [],
    }
    if score is not None:
        card["score"] = score
    if reasons is not None:
        card["reasons"] = reasons
    return card


def _score_target_flow(item: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    def add(delta: int, reason: str) -> None:
        nonlocal score
        score += delta
        if reason not in reasons:
            reasons.append(reason)

    method = str(item.get("method") or "").upper()
    path = str(item.get("path") or "").lower()
    url = str(item.get("url") or "").lower()
    haystack = f"{path} {url}"
    tags = {str(tag).lower() for tag in (item.get("tags") or [])}
    status = item.get("statusCode")
    try:
        status_int = int(status) if status is not None else None
    except Exception:
        status_int = None

    if tags:
        for tag in sorted(tags):
            if tag in {"auth", "upload", "api"}:
                add(8, f"tag:{tag}")
            elif tag not in {"static"}:
                add(3, f"tag:{tag}")

    if any(k in haystack for k in ("login", "auth", "oauth", "sso", "cas", "saml", "token", "session", "signin", "logout")):
        add(12, "auth/session endpoint")
    if any(k in haystack for k in ("/api/", "/apis/", "/graphql", "/rpc", "/v1/", "/v2/", "/rest/")):
        add(8, "api/rpc endpoint")
    if any(k in haystack for k in ("upload", "import", "attach", "avatar", "file", "multipart")):
        add(10, "upload/import/file endpoint")
    if any(k in haystack for k in ("download", "export", "report", "excel", "pdf", "template")):
        add(7, "download/export endpoint")
    if any(k in haystack for k in ("admin", "manage", "permission", "role", "user", "config", "setting")):
        add(7, "admin/permission/config endpoint")
    if any(k in haystack for k in ("swagger", "openapi", "api-docs", "actuator", "debug", "trace")):
        add(9, "metadata/debug endpoint")
    if any(k in haystack for k in ("redirect", "callback", "returnurl", "return_url", "next=", "url=")):
        add(5, "redirect/callback parameter")
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        add(6, "state-changing method")
    if status_int in {401, 403}:
        add(5, "authz boundary status")
    elif status_int is not None and 500 <= status_int <= 599:
        add(6, "server error status")
    elif status_int is not None and 300 <= status_int <= 399:
        add(2, "redirect status")
    if item.get("toolType"):
        tool = str(item.get("toolType"))
        if tool.lower() in {"scanner", "extensions", "intruder", "repeater"}:
            add(3, f"burp tool:{tool}")

    return score, reasons


def _edits_payload(
    method: str | None = None,
    path: str | None = None,
    target_host: str | None = None,
    target_port: int | None = None,
    use_https: bool | None = None,
    headers: dict[str, str] | None = None,
    add_headers: dict[str, str] | None = None,
    remove_headers: list[str] | None = None,
    body: str | None = None,
    path_replace_from: str | None = None,
    path_replace_to: str | None = None,
    body_replace_from: str | None = None,
    body_replace_to: str | None = None,
    status_code: int | None = None,
    reason_phrase: str | None = None,
) -> dict[str, Any]:
    return {
        "method": method,
        "path": path,
        "targetHost": target_host,
        "targetPort": target_port,
        "useHttps": use_https,
        "headers": headers,
        "addHeaders": add_headers,
        "removeHeaders": remove_headers,
        "body": body,
        "pathReplaceFrom": path_replace_from,
        "pathReplaceTo": path_replace_to,
        "bodyReplaceFrom": body_replace_from,
        "bodyReplaceTo": body_replace_to,
        "statusCode": status_code,
        "reasonPhrase": reason_phrase,
    }


@mcp.tool()
def burp_bridge_status() -> dict[str, Any]:
    """检查 Windows Burp 侧桥接状态、Burp 版本、实时缓冲区容量、规则数量与当前监听地址。"""
    return _request_json("/health")


@mcp.tool()
def burp_config_get() -> dict[str, Any]:
    """读取 Burp 扩展当前配置。适合确认端口、body 截断、scope-only、静态资源过滤和规则数量。"""
    return _request_json("/api/config")


@mcp.tool()
def burp_live_poll(
    after_seq: int = 0,
    limit: int = 20,
    text: str | None = None,
    host: str | None = None,
    path: str | None = None,
    method: str | None = None,
    has_response: bool | None = None,
    in_scope: bool | None = None,
    include_bodies: bool = False,
) -> dict[str, Any]:
    """从实时 ring buffer 增量读取 Burp Proxy 流量。优先用这个做低噪声轮询，再按 flowId 拉详情。"""
    return _request_json(
        "/api/flows",
        query={
            "afterSeq": after_seq,
            "limit": limit,
            "text": text,
            "host": host,
            "path": path,
            "method": method,
            "hasResponse": has_response,
            "inScope": in_scope,
            "includeBodies": include_bodies,
        },
    )


@mcp.tool()
def burp_flow_get(flow_id: int, source: str = "live", include_bodies: bool = True) -> dict[str, Any]:
    """读取单条流量的完整细节。source=live/history/selection。"""
    if source not in {"live", "history", "selection"}:
        raise ValueError("source 必须是 live、history 或 selection")
    if source == "live":
        path = f"/api/flows/{flow_id}"
    elif source == "history":
        path = f"/api/history/{flow_id}"
    else:
        path = f"/api/selection/flows/{flow_id}"
    return _request_json(path, query={"includeBodies": include_bodies})


@mcp.tool()
def burp_logger_poll(
    after_seq: int = 0,
    limit: int = 20,
    text: str | None = None,
    host: str | None = None,
    path: str | None = None,
    method: str | None = None,
    tool_type: str | None = None,
    has_response: bool | None = None,
    in_scope: bool | None = None,
    include_bodies: bool = False,
) -> dict[str, Any]:
    """读取 Burp 内部 HTTP 工具流量（logger-like）。适合看 Repeater/Intruder/Scanner/插件 fuzz 等非 Proxy 面板流量。"""
    return _request_json(
        "/api/logger/flows",
        query={
            "afterSeq": after_seq,
            "limit": limit,
            "text": text,
            "host": host,
            "path": path,
            "method": method,
            "toolType": tool_type,
            "hasResponse": has_response,
            "inScope": in_scope,
            "includeBodies": include_bodies,
        },
    )


@mcp.tool()
def burp_logger_flow_get(flow_id: int, include_bodies: bool = True) -> dict[str, Any]:
    """读取单条 Burp 内部 HTTP 工具流量详情。"""
    return _request_json(f"/api/logger/flows/{flow_id}", query={"includeBodies": include_bodies})


@mcp.tool()
def burp_selection_poll(
    after_seq: int = 0,
    limit: int = 20,
    text: str | None = None,
    host: str | None = None,
    path: str | None = None,
    method: str | None = None,
    has_response: bool | None = None,
    include_bodies: bool = False,
) -> dict[str, Any]:
    """读取 Burp HotKey/command-palette 捕获的选中流量。人在 Burp 中选中后触发 Capture selection for AI，再由 AI 拉取。"""
    return _request_json(
        "/api/selection/flows",
        query={
            "afterSeq": after_seq,
            "limit": limit,
            "text": text,
            "host": host,
            "path": path,
            "method": method,
            "hasResponse": has_response,
            "includeBodies": include_bodies,
        },
    )


@mcp.tool()
def burp_selection_get(flow_id: int, include_bodies: bool = True) -> dict[str, Any]:
    """读取一条由 Burp HotKey/command-palette 捕获的 selection flow 详情。"""
    return burp_flow_get(flow_id=flow_id, source="selection", include_bodies=include_bodies)


@mcp.tool()
def burp_history_search(
    query: str | None = None,
    regex: bool = False,
    limit: int = 20,
    offset: int = 0,
    host_contains: str | None = None,
    path_contains: str | None = None,
    method: str | None = None,
    in_scope: bool | None = None,
    has_response: bool | None = None,
    status_min: int | None = None,
    status_max: int | None = None,
    include_bodies: bool = False,
    ignore_static: bool | None = True,
) -> dict[str, Any]:
    """搜索 Burp 全量 Proxy 历史。适合查旧流量、按关键字回溯登录/API/upload 等关键链路。"""
    return _request_json(
        "/api/history/search",
        method="POST",
        payload={
            "query": query,
            "regex": regex,
            "limit": limit,
            "offset": offset,
            "hostContains": host_contains,
            "pathContains": path_contains,
            "method": method,
            "inScope": in_scope,
            "hasResponse": has_response,
            "statusMin": status_min,
            "statusMax": status_max,
            "includeBodies": include_bodies,
            "ignoreStatic": ignore_static,
        },
    )


@mcp.tool()
def burp_send_to_repeater(flow_id: int, source: str = "live", tab_name: str = "AI review") -> dict[str, Any]:
    """把选中的请求发到 Burp Repeater，方便继续手工验证或配合 AI 给出的下一步变体。"""
    if source not in {"live", "history", "logger", "selection"}:
        raise ValueError("source 必须是 live、history、logger 或 selection")
    return _request_json(
        "/api/actions/send-to-repeater",
        method="POST",
        payload={"id": flow_id, "source": source, "tabName": tab_name},
    )


@mcp.tool()
def burp_clear_live_buffer() -> dict[str, Any]:
    """清空实时流量缓冲区，适合开始一个新的验证阶段前先降噪。"""
    return _request_json("/api/actions/clear-buffer", method="POST", payload={})


@mcp.tool()
def burp_clear_logger_buffer() -> dict[str, Any]:
    """清空 Burp 内部工具/logger-like 流量缓冲区。适合在 fuzz、重放或规则联调前先降噪。"""
    return _request_json("/api/actions/clear-logger-buffer", method="POST", payload={})


@mcp.tool()
def burp_clear_selection_buffer() -> dict[str, Any]:
    """清空 HotKey/command-palette selection buffer。"""
    return _request_json("/api/actions/clear-selection-buffer", method="POST", payload={})


@mcp.tool()
def burp_export_flow_bundle(flow_id: int, source: str = "history") -> dict[str, Any]:
    """导出一条 flow 的完整原始 request/response 到 bridge 所在主机的临时目录。适合超大包场景下安全取证。"""
    if source not in {"live", "history", "logger", "selection"}:
        raise ValueError("source 必须是 live、history、logger 或 selection")
    return _request_json(
        "/api/actions/export-flow-bundle",
        method="POST",
        payload={"id": flow_id, "source": source},
    )


@mcp.tool()
def burp_live_overview(after_seq: int = 0, limit: int = 80) -> dict[str, Any]:
    """快速汇总最近实时流量，按主机、状态码、标签统计，便于 AI 先做渗透流量定向。"""
    data = burp_live_poll(after_seq=after_seq, limit=limit, include_bodies=False)
    items = data.get("items", [])
    host_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    tag_counter: Counter[str] = Counter()
    interesting_by_host: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item in items:
        host = item.get("host") or "<unknown>"
        host_counter[host] += 1
        status = item.get("statusCode")
        status_counter[str(status) if status is not None else "pending"] += 1
        for tag in item.get("tags", []):
            tag_counter[tag] += 1
        if len(interesting_by_host[host]) < 5:
            interesting_by_host[host].append(
                {
                    "flowId": item.get("flowId"),
                    "method": item.get("method"),
                    "path": item.get("path"),
                    "statusCode": item.get("statusCode"),
                    "tags": item.get("tags"),
                    "requestRuleHits": item.get("requestRuleHits", []),
                    "responseRuleHits": item.get("responseRuleHits", []),
                }
            )

    return {
        "ok": True,
        "item": {
            "count": len(items),
            "latestCursor": data.get("latestCursor"),
            "byHost": host_counter.most_common(),
            "byStatus": status_counter.most_common(),
            "byTag": tag_counter.most_common(),
            "interestingByHost": dict(interesting_by_host),
        },
    }


@mcp.tool()
def burp_logger_overview(after_seq: int = 0, limit: int = 80) -> dict[str, Any]:
    """快速汇总 Burp 内部工具流量，尤其适合看 fuzz 插件/Repeater/Intruder/Scanner 的请求响应。"""
    data = burp_logger_poll(after_seq=after_seq, limit=limit, include_bodies=False)
    items = data.get("items", [])
    host_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    tool_counter: Counter[str] = Counter()
    interesting_by_tool: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for item in items:
        host = item.get("host") or "<unknown>"
        host_counter[host] += 1
        status = item.get("statusCode")
        status_counter[str(status) if status is not None else "pending"] += 1
        tool = item.get("toolType") or "<unknown>"
        tool_counter[tool] += 1
        if len(interesting_by_tool[tool]) < 5:
            interesting_by_tool[tool].append(
                {
                    "flowId": item.get("flowId"),
                    "method": item.get("method"),
                    "path": item.get("path"),
                    "statusCode": item.get("statusCode"),
                    "host": item.get("host"),
                }
            )

    return {
        "ok": True,
        "item": {
            "count": len(items),
            "latestCursor": data.get("latestCursor"),
            "byHost": host_counter.most_common(),
            "byStatus": status_counter.most_common(),
            "byToolType": tool_counter.most_common(),
            "interestingByToolType": dict(interesting_by_tool),
        },
    }


@mcp.tool()
def burp_target_overview(
    host: str | None = None,
    text: str | None = None,
    path: str | None = None,
    sources: str = "all",
    limit: int = 80,
    include_static: bool = False,
    include_extensions: bool = True,
    candidate_limit: int = 20,
) -> dict[str, Any]:
    """按被测目标聚合 live/history/logger/selection 流量。适合 AI 围绕一个 host 做入口、接口、状态码和高价值候选请求画像。"""
    selected_sources = _parse_source_csv(sources)
    per_source_limit = max(1, min(limit, 200))
    max_candidates = max(1, min(candidate_limit, 50))
    collected: list[dict[str, Any]] = []
    source_errors: dict[str, str] = {}

    if "history" in selected_sources:
        try:
            data = burp_history_search(
                query=text,
                limit=per_source_limit,
                host_contains=host,
                path_contains=path,
                include_bodies=False,
                ignore_static=not include_static,
            )
            collected.extend(data.get("items", []))
        except Exception as exc:
            source_errors["history"] = str(exc)

    if "live" in selected_sources:
        try:
            data = burp_live_poll(
                limit=per_source_limit,
                text=text,
                host=host,
                path=path,
                include_bodies=False,
            )
            items = data.get("items", [])
            if not include_static:
                items = [item for item in items if not _is_static_path(item.get("path"))]
            collected.extend(items)
        except Exception as exc:
            source_errors["live"] = str(exc)

    if "logger" in selected_sources:
        try:
            data = burp_logger_poll(
                limit=per_source_limit,
                text=text,
                host=host,
                path=path,
                include_bodies=False,
            )
            items = data.get("items", [])
            if not include_extensions:
                items = [item for item in items if str(item.get("toolType") or "").lower() != "extensions"]
            if not include_static:
                items = [item for item in items if not _is_static_path(item.get("path"))]
            collected.extend(items)
        except Exception as exc:
            source_errors["logger"] = str(exc)

    if "selection" in selected_sources:
        try:
            data = burp_selection_poll(
                limit=per_source_limit,
                text=text,
                host=host,
                path=path,
                include_bodies=False,
            )
            items = data.get("items", [])
            if not include_static:
                items = [item for item in items if not _is_static_path(item.get("path"))]
            collected.extend(items)
        except Exception as exc:
            source_errors["selection"] = str(exc)

    by_source: Counter[str] = Counter()
    by_host: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    by_method: Counter[str] = Counter()
    by_tool_type: Counter[str] = Counter()
    by_tag: Counter[str] = Counter()
    by_endpoint: Counter[str] = Counter()
    endpoint_samples: dict[str, dict[str, Any]] = {}
    interesting: list[dict[str, Any]] = []
    seen_candidate_keys: set[tuple[str, Any]] = set()

    for item in collected:
        source = _counter_key(item.get("source"))
        by_source[source] += 1
        by_host[_counter_key(item.get("host"))] += 1
        by_method[_counter_key(item.get("method"))] += 1
        by_status[_counter_key(item.get("statusCode"), "pending")] += 1
        tool_type = item.get("toolType")
        if tool_type:
            by_tool_type[str(tool_type)] += 1
        for tag in item.get("tags") or []:
            by_tag[str(tag)] += 1

        endpoint_key = f"{_counter_key(item.get('method'), '?')} {_normalize_endpoint_path(item.get('path'))}"
        by_endpoint[endpoint_key] += 1
        endpoint_samples.setdefault(endpoint_key, _flow_card(item))

        score, reasons = _score_target_flow(item)
        if score > 0:
            key = (source, item.get("flowId"))
            if key in seen_candidate_keys:
                continue
            seen_candidate_keys.add(key)
            interesting.append(_flow_card(item, source=source, reasons=reasons, score=score))

    interesting.sort(key=lambda card: (-int(card.get("score") or 0), str(card.get("source")), int(card.get("flowId") or 0)))
    top_endpoints = [
        {
            "endpoint": endpoint,
            "count": count,
            "sample": endpoint_samples.get(endpoint),
        }
        for endpoint, count in by_endpoint.most_common(40)
    ]

    next_steps = [
        "Pick a highValueCandidate and inspect exact request/response with the matching getter: source=history/live -> burp_flow_get, source=logger -> burp_logger_flow_get, source=selection -> burp_selection_get.",
        "Replay only one variable at a time with burp_replay_flow(source=...) after confirming the baseline response.",
        "If a pattern is reusable, promote it into burp_rule_upsert, burp_bcheck_import, or burp_bambda_import instead of keeping ad-hoc manual steps.",
    ]
    if not host:
        next_steps.insert(0, "Pass host='target.example' for a tighter per-unit view; without host this is only a broad recent/history snapshot.")

    return {
        "ok": True,
        "item": {
            "purpose": "Target-centric traffic map across Proxy history, live Proxy buffer, Burp tool/logger traffic and UI selection.",
            "filters": {
                "host": host,
                "text": text,
                "path": path,
                "sources": selected_sources,
                "perSourceLimit": per_source_limit,
                "includeStatic": include_static,
                "includeExtensions": include_extensions,
            },
            "count": len(collected),
            "sourceErrors": source_errors,
            "bySource": by_source.most_common(),
            "byHost": by_host.most_common(30),
            "byStatus": by_status.most_common(),
            "byMethod": by_method.most_common(),
            "byToolType": by_tool_type.most_common(),
            "byTag": by_tag.most_common(),
            "topEndpoints": top_endpoints,
            "highValueCandidates": interesting[:max_candidates],
            "nextSteps": next_steps,
        },
    }


@mcp.tool()
def burp_extension_activity_overview(
    after_seq: int = 0,
    limit: int = 80,
    host: str | None = None,
    path: str | None = None,
    text: str | None = None,
    include_sample_details: bool = False,
    sample_limit: int = 5,
) -> dict[str, Any]:
    """聚合其他 Burp 扩展产生的 HTTP 流量，帮助 AI 从已加载插件的探测手法中提取线索；不直接调用插件内部接口。"""
    data = burp_logger_poll(
        after_seq=after_seq,
        limit=limit,
        text=text,
        host=host,
        path=path,
        tool_type="Extensions",
        include_bodies=False,
    )
    items = data.get("items", [])
    host_counter: Counter[str] = Counter()
    path_counter: Counter[str] = Counter()
    status_counter: Counter[str] = Counter()
    method_counter: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []

    for item in items:
        item_host = item.get("host") or "<unknown>"
        item_path = item.get("path") or "<unknown>"
        host_counter[item_host] += 1
        path_counter[f"{item.get('method') or '?'} {item_path}"] += 1
        method_counter[item.get("method") or "<unknown>"] += 1
        status = item.get("statusCode")
        status_counter[str(status) if status is not None else "pending"] += 1
        if len(candidates) < max(1, min(sample_limit, 20)):
            candidates.append(
                {
                    "flowId": item.get("flowId"),
                    "method": item.get("method"),
                    "host": item_host,
                    "path": item_path,
                    "statusCode": item.get("statusCode"),
                    "mimeType": item.get("mimeType"),
                    "tags": item.get("tags"),
                }
            )

    sample_details: list[dict[str, Any]] = []
    if include_sample_details:
        for candidate in candidates[: max(1, min(sample_limit, 10))]:
            flow_id = candidate.get("flowId")
            if flow_id is None:
                continue
            try:
                detail = burp_logger_flow_get(flow_id=int(flow_id), include_bodies=False).get("item", {})
                request = detail.get("request") or {}
                response = detail.get("response") or {}
                sample_details.append(
                    {
                        "flowId": flow_id,
                        "requestStartLine": request.get("startLine"),
                        "requestHeaderCount": request.get("headerCount"),
                        "requestBodyBytes": request.get("bodyBytes"),
                        "responseStartLine": response.get("startLine") if response else None,
                        "responseContentType": response.get("contentType") if response else None,
                        "responseBodyBytes": response.get("bodyBytes") if response else None,
                    }
                )
            except Exception as exc:
                sample_details.append({"flowId": flow_id, "error": str(exc)})

    return {
        "ok": True,
        "item": {
            "purpose": "Infer useful testing ideas from HTTP traffic generated by other loaded Burp extensions.",
            "directPluginInvocationSupported": False,
            "count": len(items),
            "latestCursor": data.get("latestCursor"),
            "byHost": host_counter.most_common(),
            "byPath": path_counter.most_common(30),
            "byStatus": status_counter.most_common(),
            "byMethod": method_counter.most_common(),
            "candidateFlows": candidates,
            "sampleDetails": sample_details if include_sample_details else None,
            "nextSteps": [
                "Use burp_logger_flow_get(flowId) on candidate flows to inspect exact plugin-generated requests.",
                "Replay promising requests with burp_replay_flow(source='logger') or convert patterns into rewrite rules/BChecks/Bambdas.",
                "For interface-level control, add a specific adapter only for plugins that expose a stable API or local endpoint."
            ],
        },
    }


@mcp.tool()
def burp_export_flow(flow_id: int, source: str = "live", include_bodies: bool = True, label: str | None = None) -> dict[str, Any]:
    """导出一条关键流量为本地 JSON 证据文件，便于归档、复盘或拼接正式漏洞报告。"""
    if source == "logger":
        detail = burp_logger_flow_get(flow_id=flow_id, include_bodies=include_bodies)
    elif source == "selection":
        detail = burp_selection_get(flow_id=flow_id, include_bodies=include_bodies)
    else:
        detail = burp_flow_get(flow_id=flow_id, source=source, include_bodies=include_bodies)
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    safe_label = (label or f"{source}-{flow_id}").replace("/", "_").replace(" ", "-")
    output_path = ARTIFACT_ROOT / f"burp-flow-{safe_label}-{_timestamp()}.json"
    output_path.write_text(json.dumps(detail, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "message": "flow exported", "flowId": flow_id, "source": source, "path": str(output_path)}


@mcp.tool()
def burp_replay_flow(
    flow_id: int,
    source: str = "history",
    method: str | None = None,
    path: str | None = None,
    target_host: str | None = None,
    target_port: int | None = None,
    use_https: bool | None = None,
    headers: dict[str, str] | None = None,
    add_headers: dict[str, str] | None = None,
    remove_headers: list[str] | None = None,
    body: str | None = None,
    path_replace_from: str | None = None,
    path_replace_to: str | None = None,
    body_replace_from: str | None = None,
    body_replace_to: str | None = None,
    apply_rules: bool = False,
    send_to_repeater: bool = False,
    repeater_tab_name: str = "AI replay",
    include_bodies: bool = True,
) -> dict[str, Any]:
    """基于 live/history 里的已有请求进行改包重发。适合 AI 修改 token、body、header、path 后快速验证。"""
    if source not in {"live", "history", "logger", "selection"}:
        raise ValueError("source 必须是 live、history、logger 或 selection")
    payload = {
        "id": flow_id,
        "source": source,
        "applyRules": apply_rules,
        "sendToRepeater": send_to_repeater,
        "repeaterTabName": repeater_tab_name,
        "includeBodies": include_bodies,
    }
    payload.update(
        _edits_payload(
            method=method,
            path=path,
            target_host=target_host,
            target_port=target_port,
            use_https=use_https,
            headers=headers,
            add_headers=add_headers,
            remove_headers=remove_headers,
            body=body,
            path_replace_from=path_replace_from,
            path_replace_to=path_replace_to,
            body_replace_from=body_replace_from,
            body_replace_to=body_replace_to,
        )
    )
    return _request_json("/api/replay/flow", method="POST", payload=payload)


@mcp.tool()
def burp_send_raw_request(
    raw_request: str,
    target_host: str,
    target_port: int,
    use_https: bool = False,
    apply_rules: bool = False,
    send_to_repeater: bool = False,
    repeater_tab_name: str = "AI raw replay",
    include_bodies: bool = True,
) -> dict[str, Any]:
    """直接发送原始 HTTP 请求文本。适合 AI 组合完整数据包后通过 Burp 内部 HTTP 栈重放。"""
    return _request_json(
        "/api/replay/raw",
        method="POST",
        payload={
            "rawRequest": raw_request,
            "targetHost": target_host,
            "targetPort": target_port,
            "useHttps": use_https,
            "applyRules": apply_rules,
            "sendToRepeater": send_to_repeater,
            "repeaterTabName": repeater_tab_name,
            "includeBodies": include_bodies,
        },
    )


@mcp.tool()
def burp_rules_list() -> dict[str, Any]:
    """列出当前启用/禁用的自动请求/响应改写规则，包含 actionSchema 说明 modify/drop/spoof 与 applyTo 语义。"""
    return _request_json("/api/rules")


@mcp.tool()
def burp_rule_upsert(
    direction: str,
    action: str = "modify",
    apply_to: str = "proxy",
    name: str | None = None,
    rule_id: str | None = None,
    enabled: bool = True,
    match_host_contains: str | None = None,
    match_path_contains: str | None = None,
    match_method: str | None = None,
    match_body_contains: str | None = None,
    match_status_min: int | None = None,
    match_status_max: int | None = None,
    method: str | None = None,
    path: str | None = None,
    target_host: str | None = None,
    target_port: int | None = None,
    use_https: bool | None = None,
    headers: dict[str, str] | None = None,
    add_headers: dict[str, str] | None = None,
    remove_headers: list[str] | None = None,
    body: str | None = None,
    path_replace_from: str | None = None,
    path_replace_to: str | None = None,
    body_replace_from: str | None = None,
    body_replace_to: str | None = None,
    status_code: int | None = None,
    reason_phrase: str | None = None,
) -> dict[str, Any]:
    """新增或更新自动规则。action=modify 改写并放行；action=drop 丢弃匹配消息；action=spoof 用规则字段构造替代响应；apply_to=proxy/tool/all 控制作用面。"""
    if direction not in {"request", "response"}:
        raise ValueError("direction 必须是 request 或 response")
    if action not in {"modify", "drop", "spoof"}:
        raise ValueError("action 必须是 modify、drop 或 spoof")
    if apply_to not in {"proxy", "tool", "all"}:
        raise ValueError("apply_to 必须是 proxy、tool 或 all")
    payload = {
        "id": rule_id,
        "name": name,
        "direction": direction,
        "action": action,
        "applyTo": apply_to,
        "enabled": enabled,
        "matchHostContains": match_host_contains,
        "matchPathContains": match_path_contains,
        "matchMethod": match_method,
        "matchBodyContains": match_body_contains,
        "matchStatusMin": match_status_min,
        "matchStatusMax": match_status_max,
    }
    payload.update(
        _edits_payload(
            method=method,
            path=path,
            target_host=target_host,
            target_port=target_port,
            use_https=use_https,
            headers=headers,
            add_headers=add_headers,
            remove_headers=remove_headers,
            body=body,
            path_replace_from=path_replace_from,
            path_replace_to=path_replace_to,
            body_replace_from=body_replace_from,
            body_replace_to=body_replace_to,
            status_code=status_code,
            reason_phrase=reason_phrase,
        )
    )
    return _request_json("/api/rules", method="POST", payload=payload)


@mcp.tool()
def burp_rule_delete(rule_id: str) -> dict[str, Any]:
    """删除一条自动改写规则。"""
    return _request_json(f"/api/rules/{urllib.parse.quote(rule_id, safe='')}", method="DELETE")


@mcp.tool()
def burp_bcheck_import(content: str | None = None, path: str | None = None, replace_existing: bool = True) -> dict[str, Any]:
    """导入 AI 生成或本地文件中的 BCheck，自定义扩展 Burp Scanner 检查项。content/path 二选一；导入后由 Burp Scanner 官方流程执行。"""
    if not content and not path:
        raise ValueError("content 或 path 必须提供一个")
    if content and path:
        raise ValueError("content 和 path 只能提供一个")
    if path:
        content = Path(path).read_text(encoding="utf-8")
    return _request_json(
        "/api/scanner/bchecks/import",
        method="POST",
        payload={"content": content, "replaceExisting": replace_existing},
    )


@mcp.tool()
def burp_bambda_import(content: str | None = None, path: str | None = None) -> dict[str, Any]:
    """导入 AI 生成或本地文件中的 Bambda 到 Burp Bambda Library。适合把自定义行动/列/过滤器脚本交给 Burp UI 管理和执行。"""
    if not content and not path:
        raise ValueError("content 或 path 必须提供一个")
    if content and path:
        raise ValueError("content 和 path 只能提供一个")
    if path:
        content = Path(path).read_text(encoding="utf-8")
    return _request_json(
        "/api/bambdas/import",
        method="POST",
        payload={"content": content},
    )


@mcp.tool()
def burp_mcp_list(section: str = "index", topic: str | None = None, detail: bool = False) -> dict[str, Any]:
    """分级列出 BurpSuite MCP Bridge 的工具用法。先 section=index 获取目录，再按 section/topic 拉取小块说明，避免一次性占满上下文。"""
    catalog = _mcp_help_catalog()
    if section in {"", "index", "root"}:
        return {
            "ok": True,
            "item": {
                "usage": "Call burp_mcp_list(section='<section>') for topics, then burp_mcp_list(section='<section>', topic='<topic>', detail=true) for focused usage.",
                "sections": [
                    {"section": key, "summary": value["summary"], "topics": list(value["topics"].keys())}
                    for key, value in catalog.items()
                ],
            },
        }
    if section not in catalog:
        return {"ok": False, "message": f"unknown section: {section}", "availableSections": list(catalog.keys())}
    section_data = catalog[section]
    if not topic:
        return {
            "ok": True,
            "item": {
                "section": section,
                "summary": section_data["summary"],
                "topics": [
                    {"topic": key, "summary": value["summary"]}
                    for key, value in section_data["topics"].items()
                ],
            },
        }
    topics = section_data["topics"]
    if topic not in topics:
        return {"ok": False, "message": f"unknown topic: {topic}", "availableTopics": list(topics.keys())}
    topic_data = topics[topic]
    item = {"section": section, "topic": topic, "summary": topic_data["summary"]}
    if detail:
        item.update(topic_data)
    else:
        item["hint"] = "Set detail=true for parameters and examples."
    return {"ok": True, "item": item}


def _mcp_help_catalog() -> dict[str, Any]:
    return {
        "traffic": {
            "summary": "Read low-noise target-centric, Proxy live/history/logger-like traffic.",
            "topics": {
                "target": {
                    "summary": "Target-centric map across history/live/logger/selection, grouped by host/status/method/tool/endpoint with high-value candidates.",
                    "tools": ["burp_target_overview", "burp_flow_get", "burp_logger_flow_get", "burp_selection_get"],
                    "params": {"host": "recommended target host filter", "sources": "all or comma-separated history,live,logger,selection", "include_extensions": "keep plugin-generated target traffic in the same target view"},
                    "example": "burp_target_overview(host='example.com', sources='all', limit=80) -> inspect one highValueCandidate",
                },
                "live": {
                    "summary": "Incremental Proxy buffer triage.",
                    "tools": ["burp_live_overview", "burp_live_poll", "burp_flow_get"],
                    "params": {"after_seq": "cursor from latestCursor", "include_bodies": "default false for triage"},
                    "example": "burp_live_overview(after_seq=0, limit=80) -> burp_flow_get(flow_id, source='live')",
                },
                "history": {
                    "summary": "Search persisted Proxy history without replaying traffic.",
                    "tools": ["burp_history_search", "burp_flow_get"],
                    "params": {"query": "plain text or regex", "host_contains/path_contains/status_min/status_max": "narrow filters"},
                    "example": "burp_history_search(host_contains='example.com', path_contains='/api', limit=20)",
                },
                "logger": {
                    "summary": "Read Burp internal HTTP tool traffic captured after extension load.",
                    "tools": ["burp_logger_overview", "burp_logger_poll", "burp_logger_flow_get"],
                    "params": {"tool_type": "Repeater/Intruder/Scanner/Extensions etc."},
                    "example": "burp_logger_poll(tool_type='Repeater', limit=20)",
                },
                "selection": {
                    "summary": "Read items captured from Burp UI selection via command palette/hotkey.",
                    "tools": ["burp_selection_poll", "burp_selection_get", "burp_flow_get"],
                    "params": {"source": "Use source='selection' with flow_get/replay/export/send_to_repeater."},
                    "example": "Trigger 'Burp MCP Bridge: Capture selection for AI' in Burp, then burp_selection_poll(limit=20)",
                },
            },
        },
        "replay": {
            "summary": "Replay captured or raw requests with controlled mutations.",
            "topics": {
                "flow": {
                    "summary": "Replay live/history request with method/path/header/body edits.",
                    "tools": ["burp_replay_flow"],
                    "params": {"apply_rules": "run rewrite rules before/after replay", "send_to_repeater": "also open request in Repeater"},
                    "example": "burp_replay_flow(flow_id=123, source='history', path_replace_from='id=1', path_replace_to='id=2')",
                },
                "raw": {
                    "summary": "Send a fully assembled raw HTTP request through Burp HTTP stack.",
                    "tools": ["burp_send_raw_request"],
                    "params": {"target_host/target_port/use_https": "required target service"},
                    "example": "burp_send_raw_request(raw_request='GET / HTTP/1.1\\r\\nHost: example.com\\r\\n\\r\\n', target_host='example.com', target_port=443, use_https=True)",
                },
            },
        },
        "rules": {
            "summary": "Automatic request/response controls with proxy/tool/all scope.",
            "topics": {
                "actions": {
                    "summary": "modify/drop/spoof semantics.",
                    "tools": ["burp_rules_list", "burp_rule_upsert", "burp_rule_delete"],
                    "params": {"action": "modify|drop|spoof", "direction": "request|response", "apply_to": "proxy|tool|all"},
                    "example": "burp_rule_upsert(direction='request', action='spoof', apply_to='proxy', match_host_contains='example.com', body='mock')",
                },
                "scope": {
                    "summary": "apply_to controls where rules run.",
                    "details": [
                        "proxy: default; only browser/client traffic through Burp Proxy.",
                        "tool: Burp internal tools such as Repeater/Intruder/Scanner when Montoya runtime supports it; extension self-replay is skipped to avoid double-apply.",
                        "all: proxy + supported internal tools."
                    ],
                },
            },
        },
        "evidence": {
            "summary": "Export decisive flows without stuffing large bodies into MCP context.",
            "topics": {
                "export": {
                    "summary": "Write JSON or raw request/response bundles to disk.",
                    "tools": ["burp_export_flow", "burp_export_flow_bundle"],
                    "params": {"source": "live|history|logger", "include_bodies": "use false for huge flows unless needed"},
                },
            },
        },
        "official": {
            "summary": "Runtime-detected Montoya 2026.4.x integrations.",
            "topics": {
                "selection": {
                    "summary": "Command palette / HotKey bridge from Burp UI selection to MCP.",
                    "tools": ["burp_selection_poll", "burp_selection_get"],
                    "details": [
                        "Registers 'Burp MCP Bridge: Capture selection for AI' where supported.",
                        "Captured items become source=selection so existing replay/export/repeater tools can operate on them.",
                        "Default hotkey is Ctrl+Alt+M; command palette discovery is preferred if a shortcut conflicts."
                    ],
                },
                "compat": {
                    "summary": "Check which optional official APIs are available in the loaded Burp runtime.",
                    "tools": ["burp_bridge_status", "burp_config_get"],
                    "details": [
                        "montoyaCompat.runtimeOptionalFeatures.httpHandlerRequestDropSpoof: official internal-tool request drop/spoof.",
                        "hotKeyApi / hotKeySelectedRequestResponses: command-palette/hotkey groundwork for later selected-row workflows."
                    ],
                },
            },
        },
        "scanner": {
            "summary": "Lightweight Scanner control-plane helpers; leave heavy scanning to Burp official Scanner.",
            "topics": {
                "bcheck": {
                    "summary": "Import AI-generated or local BCheck content into Burp Scanner custom checks.",
                    "tools": ["burp_bcheck_import"],
                    "params": {"content": "BCheck source text", "path": "local MCP-side .bcheck file", "replace_existing": "default true"},
                    "example": "burp_bcheck_import(path='/tmp/check.bcheck', replace_existing=True)",
                },
            },
        },
        "bambda": {
            "summary": "Import scripts into Burp Bambda Library; Burp UI remains the execution surface.",
            "topics": {
                "import": {
                    "summary": "Import AI-generated or local Bambda content for custom actions, columns, filters, match/replace, or scan checks.",
                    "tools": ["burp_bambda_import"],
                    "params": {"content": "Bambda script text", "path": "local MCP-side Bambda file"},
                    "example": "burp_bambda_import(path='/tmp/custom-action.bambda')",
                },
                "strategy": {
                    "summary": "Use MCP as a script delivery/control plane, not a duplicate Bambda executor.",
                    "details": [
                        "Custom actions in Repeater are Bambda-backed workflows; import the script, then run it in Burp where the selected message/context exists.",
                        "For quick AI automation on captured traffic, prefer MCP replay/rules/selection. For reusable UI workflows, import a Bambda.",
                        "Bambda scripts can execute code, so keep imports explicit and review generated scripts before enabling them broadly."
                    ],
                },
            },
        },
        "plugins": {
            "summary": "Observe and learn from other loaded Burp extensions without pretending to call their private APIs.",
            "topics": {
                "activity": {
                    "summary": "Cluster HTTP traffic generated by other extensions and return candidate flowIds for AI analysis.",
                    "tools": ["burp_extension_activity_overview", "burp_logger_flow_get", "burp_replay_flow"],
                    "params": {"tool_type": "Internally uses logger-like ToolType=Extensions", "include_sample_details": "small metadata only, no large bodies"},
                    "example": "burp_extension_activity_overview(limit=80, include_sample_details=True)",
                },
                "adapters": {
                    "summary": "Interface-level plugin control is only realistic for known/cooperating plugins.",
                    "details": [
                        "Generic Montoya does not expose a stable API to enumerate and call arbitrary extension internals.",
                        "Best generic path: observe extension-generated traffic and convert useful behavior into MCP replay/rules/BChecks/Bambdas.",
                        "For specific plugins that expose local HTTP/RPC/config files, add explicit adapter tools instead of unsafe reflection."
                    ],
                },
            },
        },
    }


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description="BurpSuite MCP Bridge server")
        parser.add_argument("--transport", choices=["stdio", "streamable-http", "sse"], default=MCP_TRANSPORT)
        parser.add_argument("--host", default=MCP_SERVER_HOST, help="Host for HTTP MCP transports")
        parser.add_argument("--port", type=int, default=MCP_SERVER_PORT, help="Port for HTTP MCP transports")
        parser.add_argument("--path", default=MCP_SERVER_PATH, help="Path for Streamable HTTP MCP transport")
        args = parser.parse_args()

        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.settings.streamable_http_path = args.path
        mcp.run(transport=args.transport)
    except Exception as exc:  # pragma: no cover
        print(f"[burpsuite-mcp-bridge] fatal: {exc}", file=os.sys.stderr)
        raise
