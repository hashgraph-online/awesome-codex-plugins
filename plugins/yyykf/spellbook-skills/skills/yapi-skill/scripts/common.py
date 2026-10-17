#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import http.client
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class YapiSkillError(RuntimeError):
    pass


def _is_windows() -> bool:
    return os.name == "nt"


def is_windows() -> bool:
    # Compatibility for test cases: allow overriding platform branch via monkeypatch _is_windows()
    return _is_windows()


def _parse_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default


def _now_ts() -> int:
    return int(time.time())


def _md_escape(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    # markdown table safety
    text = text.replace("|", "\\|")
    # keep tables single-line
    text = text.replace("\r\n", "\n").replace("\n", "<br>")
    return text


def _redact_url(url: str, redact_keys: Iterable[str] = ("token",)) -> str:
    try:
        parsed = urllib.parse.urlsplit(url)
        query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        redacted: List[Tuple[str, str]] = []
        for k, v in query:
            if k in set(redact_keys):
                redacted.append((k, "***"))
            else:
                redacted.append((k, v))
        new_query = urllib.parse.urlencode(redacted)
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))
    except Exception:
        return "<redacted-url>"


def default_config_path() -> Path:
    return resolve_default_config_path()


def resolve_default_config_path() -> Path:
    env_path = os.environ.get("YAPI_SKILL_CONFIG")
    if env_path:
        return Path(env_path).expanduser()

    if is_windows():
        appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if appdata:
            # Keep Windows-style separator for easy string assertions in non-Windows test environments
            return Path(f"{appdata}\\yapi-skill-config\\config.json")

    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "yapi-skill-config" / "config.json"

    return Path.home() / ".config" / "yapi-skill-config" / "config.json"


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _read_json_file(path: Path) -> Dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise YapiSkillError(
            f"Configuration file not found: {path}\n"
            "Please run the initialization script first to generate the config file (see skills/yapi-skill/SKILL.md):\n"
            "python3 skills/yapi-skill/scripts/init_config.py"
        ) from e
    except OSError as e:
        raise YapiSkillError(f"Failed to read config file: {path}, reason: {e}") from e

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise YapiSkillError(f"Config file is not valid JSON: {path}, reason: {e}") from e

    if not isinstance(data, dict):
        raise YapiSkillError(f"Config file format error, expected JSON Object: {path}")

    return data


def _write_json_file_secure(path: Path, data: Dict[str, Any]) -> None:
    ensure_parent_dir(path)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)

    # Try to tighten permissions (chmod may be ineffective on Windows)
    try:
        if not is_windows():
            os.chmod(path, 0o600)
    except Exception:
        pass


def normalize_base_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        raise YapiSkillError("Config item base_url cannot be empty")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise YapiSkillError("Config item base_url must start with http:// or https://")

    parsed = urllib.parse.urlsplit(url)
    if not parsed.scheme or not parsed.netloc:
        raise YapiSkillError("Config item base_url format error (missing domain)")

    origin = f"{parsed.scheme}://{parsed.netloc}"

    # Many new users directly paste the "interface page URL" into base_url (e.g., /project/... or #/project/...).
    # Add a layer of fault tolerance here: recognize common YApi UI routes and automatically truncate to origin.
    path = parsed.path or ""
    frag = parsed.fragment or ""
    if path.startswith("/project/") or path.startswith("/group/") or path.startswith("/interface/"):
        return origin
    if frag.startswith("/project/") or frag.startswith("project/") or "/project/" in frag:
        return origin

    base_path = (path or "").rstrip("/")
    if not base_path or base_path == "/":
        return origin
    return origin + base_path


_INTERFACE_URL_RE = re.compile(r"/project/(?P<project_id>\d+)/interface/api/(?P<interface_id>\d+)")


def parse_interface_url(url: str) -> Tuple[int, int]:
    """
    Parse YApi interface page URL, extract (project_id, interface_id).

    Supported examples:
    - http://yapi.example.com/project/1650/interface/api/414469
    - http://yapi.example.com/#/project/1650/interface/api/414469
    """
    raw = (url or "").strip()
    if not raw:
        raise YapiSkillError("Interface URL cannot be empty")

    parsed = urllib.parse.urlsplit(raw)

    for candidate in (parsed.path or "", parsed.fragment or ""):
        m = _INTERFACE_URL_RE.search(candidate)
        if not m:
            continue
        try:
            return int(m.group("project_id")), int(m.group("interface_id"))
        except Exception as e:
            raise YapiSkillError(f"Failed to parse interface URL: {raw}") from e

    raise YapiSkillError(
        "Failed to parse projectId/interfaceId from interface URL.\n"
        "Expected format: .../project/<projectId>/interface/api/<interfaceId>"
    )


@dataclass(frozen=True)
class YapiConfig:
    base_url: str
    project_tokens: Dict[str, str]
    timeout_seconds: int = 60
    verify_tls: bool = True
    search_page_size: int = 2000
    search_max_pages: int = 10

    @staticmethod
    def from_dict(raw: Dict[str, Any]) -> "YapiConfig":
        base_url = normalize_base_url(str(raw.get("base_url", "")).strip())

        tokens_raw = raw.get("project_tokens")
        if not isinstance(tokens_raw, dict) or not tokens_raw:
            raise YapiSkillError("Config item project_tokens cannot be empty, and must be an object mapping {\"project_id\": \"token\"}")

        project_tokens: Dict[str, str] = {}
        for k, v in tokens_raw.items():
            key = str(k).strip()
            val = str(v).strip()
            if not key or not val:
                continue
            project_tokens[key] = val

        if not project_tokens:
            raise YapiSkillError("Config item project_tokens cannot be empty (configure at least one project token)")

        http_raw = raw.get("http") if isinstance(raw.get("http"), dict) else {}
        timeout_seconds = int(http_raw.get("timeout_seconds", 60) or 60)
        verify_tls = _parse_bool(http_raw.get("verify_tls", True), True)

        search_raw = raw.get("search") if isinstance(raw.get("search"), dict) else {}
        search_page_size = int(search_raw.get("page_size", 2000) or 2000)
        search_max_pages = int(search_raw.get("max_pages", 10) or 10)

        return YapiConfig(
            base_url=base_url,
            project_tokens=project_tokens,
            timeout_seconds=timeout_seconds,
            verify_tls=verify_tls,
            search_page_size=search_page_size,
            search_max_pages=search_max_pages,
        )


def load_config(config_path: Optional[Path] = None) -> Tuple[YapiConfig, Path]:
    path = (config_path or default_config_path()).expanduser()
    raw = _read_json_file(path)
    return YapiConfig.from_dict(raw), path


def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> Path:
    path = (config_path or default_config_path()).expanduser()
    _write_json_file_secure(path, config)
    return path


def print_json(data: Any) -> None:
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")


def _build_url(base_url: str, api_path: str, params: Dict[str, Any]) -> str:
    qs = urllib.parse.urlencode({k: str(v) for k, v in params.items() if v is not None})
    return f"{base_url}{api_path}?{qs}"


def http_get_json(url: str, timeout_seconds: int, verify_tls: bool) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "yapi-skill/1.0",
        },
        method="GET",
    )

    context = None
    if not verify_tls and url.lower().startswith("https://"):
        context = ssl._create_unverified_context()

    max_attempts = 3
    body: bytes = b""
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds, context=context) as resp:
                body = resp.read()
            break
        except urllib.error.HTTPError as e:
            redacted = _redact_url(url)
            try:
                raw = e.read()
                detail = raw.decode("utf-8", errors="replace")
            except Exception:
                detail = "<no-body>"
            raise YapiSkillError(f"HTTP request failed: {e.code} {e.reason}, URL={redacted}, response={detail}") from e
        except (
            urllib.error.URLError,
            http.client.RemoteDisconnected,
            ConnectionResetError,
            TimeoutError,
        ) as e:
            if attempt < max_attempts:
                # Simple backoff to improve success rate in weak network/occasional disconnection scenarios
                time.sleep(0.3 * attempt)
                continue
            redacted = _redact_url(url)
            raise YapiSkillError(f"Network request failed: URL={redacted}, reason: {e} (retried {attempt} times)") from e

    try:
        text = body.decode("utf-8")
    except Exception:
        text = body.decode("utf-8", errors="replace")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        redacted = _redact_url(url)
        raise YapiSkillError(f"Response is not valid JSON: URL={redacted}, reason: {e}, response snippet={text[:200]}") from e

    if not isinstance(data, dict):
        raise YapiSkillError("Response JSON structure anomaly: expected Object")
    return data


def _http_write_raw(
    url: str,
    data: bytes,
    content_type: str,
    timeout_seconds: int,
    verify_tls: bool,
) -> Dict[str, Any]:
    """POST a pre-encoded body to a YApi write endpoint, parse the JSON reply.

    Shared by http_post_form / http_post_json. Unlike http_get_json, write
    requests are NOT retried: `add` is not idempotent, so a blind retry could
    create duplicate interfaces.
    """
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Accept": "application/json",
            "Content-Type": content_type,
            "User-Agent": "yapi-skill/1.0",
        },
        method="POST",
    )

    context = None
    if not verify_tls and url.lower().startswith("https://"):
        context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds, context=context) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        redacted = _redact_url(url)
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            detail = "<no-body>"
        raise YapiSkillError(f"HTTP write failed: {e.code} {e.reason}, URL={redacted}, response={detail}") from e
    except (urllib.error.URLError, http.client.RemoteDisconnected, ConnectionResetError, TimeoutError) as e:
        redacted = _redact_url(url)
        raise YapiSkillError(f"Network write failed: URL={redacted}, reason: {e}") from e

    text = raw.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        redacted = _redact_url(url)
        raise YapiSkillError(f"Write response is not valid JSON: URL={redacted}, reason: {e}, snippet={text[:200]}") from e
    if not isinstance(parsed, dict):
        raise YapiSkillError("Write response JSON structure anomaly: expected Object")
    return parsed


def http_post_form(
    url: str,
    fields: Dict[str, Any],
    timeout_seconds: int,
    verify_tls: bool,
) -> Dict[str, Any]:
    """POST application/x-www-form-urlencoded to a YApi write endpoint.

    For endpoints whose body is flat scalars only — e.g. /api/interface/add_cat,
    which the OpenAPI doc specifies as form-urlencoded. Do NOT use this for
    add/up: their array fields (req_query/req_headers/req_params/req_body_form/
    tag) cannot survive form encoding — they get JSON-stringified to e.g. "[]"
    and YApi rejects them ("应当是 array 类型"). Use http_post_json instead.
    """
    body_pairs: List[Tuple[str, str]] = []
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, bool):
            body_pairs.append((k, "true" if v else "false"))
        elif isinstance(v, (dict, list)):
            body_pairs.append((k, json.dumps(v, ensure_ascii=False)))
        else:
            body_pairs.append((k, str(v)))
    data = urllib.parse.urlencode(body_pairs).encode("utf-8")
    return _http_write_raw(url, data, "application/x-www-form-urlencoded; charset=utf-8", timeout_seconds, verify_tls)


def http_post_json(
    url: str,
    payload: Dict[str, Any],
    timeout_seconds: int,
    verify_tls: bool,
) -> Dict[str, Any]:
    """POST application/json to a YApi write endpoint.

    Required for /api/interface/add and /api/interface/up: their bodies carry
    array fields (req_query/req_headers/req_params/req_body_form/tag) that YApi
    validates as real JSON arrays. form-urlencoded would serialize them to
    strings like "[]" and YApi rejects that. JSON body keeps arrays/bools/
    nested objects as-is. `None` values are dropped so callers can omit a field
    by leaving it None (mirrors http_post_form).
    """
    body = {k: v for k, v in payload.items() if v is not None}
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    return _http_write_raw(url, data, "application/json; charset=utf-8", timeout_seconds, verify_tls)


def yapi_extract_data(resp: Dict[str, Any]) -> Any:
    if "errcode" not in resp:
        raise YapiSkillError("Yapi response missing errcode field")
    try:
        errcode = int(resp.get("errcode"))
    except Exception as e:
        raise YapiSkillError(f"Yapi response errcode invalid: {resp.get('errcode')}") from e
    errmsg = resp.get("errmsg")
    if errcode != 0:
        message = f"Yapi returned error: errcode={errcode} errmsg={errmsg}"
        errmsg_s = str(errmsg or "")
        if errcode == 40011 or ("\u8bf7\u767b\u5f55" in errmsg_s):  # "\u8bf7\u767b\u5f55" is "Please login" in Chinese
            message += (
                "\n\n"
                "Hint: This error is usually related to authentication (token missing/invalid/unauthorized).\n"
                "- Check if project_tokens in the config file contains the current projectId\n"
                "- Ensure you copied the correct project token (OpenAPI token) from YApi project settings\n"
                "- Ensure base_url points to the correct YApi environment (do not include paths like /project/...)"
            )
        raise YapiSkillError(message)
    if "data" not in resp:
        raise YapiSkillError("Yapi response missing data field")
    data = resp.get("data")
    if data is None:
        raise YapiSkillError("Yapi response data is empty")
    return data


def parse_yapi_response(resp: Dict[str, Any]) -> Any:
    # Compatibility with test case naming: keep parse_yapi_response()
    return yapi_extract_data(resp)


def get_token(config: YapiConfig, project_id: int) -> str:
    token = config.project_tokens.get(str(project_id))
    if not token:
        raise YapiSkillError(f"Token config not found for project ID {project_id}")
    return token


def iter_project_tokens(config: YapiConfig) -> List[Tuple[int, str]]:
    items: List[Tuple[int, str]] = []
    for k, v in config.project_tokens.items():
        try:
            project_id = int(k)
        except ValueError as e:
            raise YapiSkillError(f"Key for project_tokens must be a numeric project ID, but found: {k}") from e
        items.append((project_id, v))
    items.sort(key=lambda x: x[0])
    return items


def yapi_get_interface_detail_raw(config: YapiConfig, interface_id: int, project_id: int) -> Dict[str, Any]:
    token = get_token(config, project_id)
    url = _build_url(config.base_url, "/api/interface/get", {"id": interface_id, "token": token})
    resp = http_get_json(url, config.timeout_seconds, config.verify_tls)
    data = yapi_extract_data(resp)
    if not isinstance(data, dict):
        raise YapiSkillError("Interface detail data structure anomaly: expected Object")
    return data


def yapi_get_project_by_token(config: YapiConfig, token: str) -> Dict[str, Any]:
    url = _build_url(config.base_url, "/api/project/get", {"token": token})
    resp = http_get_json(url, config.timeout_seconds, config.verify_tls)
    data = yapi_extract_data(resp)
    if not isinstance(data, dict):
        raise YapiSkillError("Project info data structure anomaly: expected Object")
    return data


def yapi_list_interfaces_raw(
    config: YapiConfig,
    project_id: int,
    page: int,
    limit: int,
) -> Dict[str, Any]:
    token = get_token(config, project_id)
    url = _build_url(
        config.base_url,
        "/api/interface/list",
        {"project_id": project_id, "token": token, "page": page, "limit": limit},
    )
    resp = http_get_json(url, config.timeout_seconds, config.verify_tls)
    data = yapi_extract_data(resp)
    if not isinstance(data, dict):
        raise YapiSkillError("Interface list data structure anomaly: expected Object")
    return data


def yapi_add_interface_raw(config: YapiConfig, project_id: int, fields: Dict[str, Any]) -> Any:
    """POST /api/interface/add. Caller supplies YApi-native fields (title/path/method/catid/req_*/res_body/markdown...)."""
    token = get_token(config, project_id)
    payload = {**fields, "token": token, "project_id": project_id}
    url = f"{config.base_url}/api/interface/add"
    resp = http_post_json(url, payload, config.timeout_seconds, config.verify_tls)
    return yapi_extract_data(resp)


def yapi_up_interface_raw(config: YapiConfig, project_id: int, fields: Dict[str, Any]) -> Any:
    """POST /api/interface/up. `fields` must include the interface `id`.

    `status` is stripped here on purpose: YApi errors out ("服务器出错") when a
    project-token `up` carries `status`, and status is human-owned content the
    sync must not touch.
    """
    token = get_token(config, project_id)
    payload = {k: v for k, v in fields.items() if k != "status"}
    payload["token"] = token
    url = f"{config.base_url}/api/interface/up"
    resp = http_post_json(url, payload, config.timeout_seconds, config.verify_tls)
    return yapi_extract_data(resp)


def yapi_get_cat_menu_raw(config: YapiConfig, project_id: int) -> List[Dict[str, Any]]:
    """GET /api/interface/getCatMenu — list a project's categories (menus)."""
    token = get_token(config, project_id)
    url = _build_url(config.base_url, "/api/interface/getCatMenu", {"project_id": project_id, "token": token})
    resp = http_get_json(url, config.timeout_seconds, config.verify_tls)
    data = yapi_extract_data(resp)
    if not isinstance(data, list):
        raise YapiSkillError("Cat menu data structure anomaly: expected Array")
    return data


def yapi_add_cat_raw(config: YapiConfig, project_id: int, name: str, desc: str = "") -> Any:
    """POST /api/interface/add_cat — create a category; returns the created cat (with _id)."""
    token = get_token(config, project_id)
    payload = {"token": token, "project_id": project_id, "name": name, "desc": desc}
    url = f"{config.base_url}/api/interface/add_cat"
    resp = http_post_form(url, payload, config.timeout_seconds, config.verify_tls)
    return yapi_extract_data(resp)


def normalize_api_path(path: str) -> str:
    """Normalize a path for matching: trim + strip trailing slash (except root).

    Case-SENSITIVE on purpose: HTTP paths are case-sensitive, and folding case
    could match a different interface (e.g. /User vs /user) and overwrite it.
    """
    s = (path or "").strip()
    if len(s) > 1 and s.endswith("/"):
        s = s.rstrip("/")
    return s


def find_interface_by_path_method(
    config: YapiConfig,
    project_id: int,
    path: str,
    method: str,
) -> Optional[Dict[str, Any]]:
    """Locate an interface within a project by exact (path, method).

    Returns the list item (containing `_id`) if exactly one matches, None if none.
    Raises if multiple match (ambiguous — caller should resolve via explicit id).
    """
    target_path = normalize_api_path(path)
    target_method = (method or "").strip().upper()
    matches: List[Dict[str, Any]] = []

    page_size = max(1, int(config.search_page_size))
    max_pages = max(1, int(config.search_max_pages))
    fully_scanned = False
    scanned_count = 0
    last_total = 0
    for page in range(1, max_pages + 1):
        data = yapi_list_interfaces_raw(config, project_id, page, page_size)
        items = data.get("list") if isinstance(data, dict) else None
        if not isinstance(items, list):
            raise YapiSkillError(
                f"Interface list response malformed for project {project_id} (page {page}): "
                "'list' is missing or not an array."
            )
        if not items:  # 空数组 = 末页
            fully_scanned = True
            break
        for it in items:
            if not isinstance(it, dict):
                continue
            if (
                normalize_api_path(str(it.get("path"))) == target_path
                and str(it.get("method") or "").strip().upper() == target_method
            ):
                matches.append(it)
        scanned_count += len(items)
        total = data.get("total") if isinstance(data, dict) else None
        try:
            last_total = int(total) if total is not None else 0
        except Exception:
            last_total = 0
        if last_total > 0 and scanned_count >= last_total:
            fully_scanned = True
            break
        if len(items) < page_size:
            # 不足一页：通常即末页（即便 total 缺失/为 0 也可据此判定完整扫描）
            fully_scanned = True
            break

    if len(matches) > 1:
        ids = [m.get("_id") for m in matches]
        raise YapiSkillError(
            f"Found {len(matches)} interfaces matching {target_method} {path} (ids={ids}); "
            "resolve manually with an explicit interfaceId."
        )
    # 未完整扫描时无法下确定结论：有候选不能证明唯一、无候选不能断定不存在 → 一律 fail closed
    if not fully_scanned:
        if matches:
            raise YapiSkillError(
                f"Found a candidate for {target_method} {path} (id={matches[0].get('_id')}) but the "
                f"interface list was not fully scanned (scanned {scanned_count} of total {last_total}, "
                f"max_pages={max_pages}); cannot prove it is the only match. "
                "Pass an explicit --interfaceId, or increase search.max_pages in config."
            )
        raise YapiSkillError(
            f"Interface list not fully scanned for project {project_id} "
            f"(scanned {scanned_count} of total {last_total}, max_pages={max_pages}); "
            f"refusing to conclude '{target_method} {path}' is absent. "
            "Increase search.max_pages in config, or pass an explicit --interfaceId."
        )
    return matches[0] if matches else None


def build_interface_detail_vo(detail: Dict[str, Any]) -> Dict[str, Any]:
    def _map_list(items: Any, mapper) -> List[Dict[str, Any]]:
        if not isinstance(items, list):
            return []
        mapped: List[Dict[str, Any]] = []
        for it in items:
            if isinstance(it, dict):
                mapped.append(mapper(it))
        return mapped

    basic_info = {
        "id": detail.get("_id"),
        "title": detail.get("title"),
        "path": detail.get("path"),
        "method": detail.get("method"),
        "projectId": detail.get("project_id"),
        "catId": detail.get("catid"),
    }

    request_info = {
        "reqBodyType": detail.get("req_body_type"),
        "reqBodyOther": detail.get("req_body_other"),
        "reqBodyForm": _map_list(
            detail.get("req_body_form"),
            lambda d: {
                "name": d.get("name"),
                "type": d.get("type"),
                "example": d.get("example"),
                "desc": d.get("desc"),
                "required": d.get("required"),
            },
        ),
        "reqParams": _map_list(
            detail.get("req_params"),
            lambda d: {"name": d.get("name"), "example": d.get("example"), "desc": d.get("desc")},
        ),
        "reqHeaders": _map_list(
            detail.get("req_headers"),
            lambda d: {
                "name": d.get("name"),
                "value": d.get("value"),
                "example": d.get("example"),
                "desc": d.get("desc"),
                "required": d.get("required"),
            },
        ),
        "reqQuery": _map_list(
            detail.get("req_query"),
            lambda d: {
                "name": d.get("name"),
                "example": d.get("example"),
                "desc": d.get("desc"),
                "required": d.get("required"),
            },
        ),
    }

    response_info = {
        "resBodyType": detail.get("res_body_type"),
        "resBody": detail.get("res_body"),
        "resBodyIsJsonSchema": bool(detail.get("res_body_is_json_schema", False)),
    }

    other_info = {"status": detail.get("status"), "markdown": detail.get("markdown")}

    return {
        "basicInfo": basic_info,
        "requestInfo": request_info,
        "responseInfo": response_info,
        "otherInfo": other_info,
    }


def _pretty_json_maybe(text: Any) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        return _md_escape(text)
    s = text.strip()
    if not s:
        return ""
    if not (s.startswith("{") or s.startswith("[")):
        return s
    try:
        obj = json.loads(s)
    except Exception:
        return s
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _render_table(rows: List[Dict[str, Any]], columns: List[Tuple[str, str]]) -> str:
    if not rows:
        return "_None_\n"
    headers = [c[0] for c in columns]
    keys = [c[1] for c in columns]
    lines = [
        "|" + "|".join(headers) + "|",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        lines.append("|" + "|".join(_md_escape(row.get(k)) for k in keys) + "|")
    return "\n".join(lines) + "\n"


def render_interface_detail_markdown(vo: Dict[str, Any]) -> str:
    basic = vo.get("basicInfo") or {}
    req = vo.get("requestInfo") or {}
    resp = vo.get("responseInfo") or {}
    other = vo.get("otherInfo") or {}

    title = basic.get("title") or ""
    method = basic.get("method") or ""
    path = basic.get("path") or ""

    out: List[str] = []
    out.append(f"# {_md_escape(title)}".strip())
    out.append("")
    out.append(f"- interfaceId: `{_md_escape(basic.get('id'))}`")
    out.append(f"- projectId: `{_md_escape(basic.get('projectId'))}`")
    out.append(f"- catId: `{_md_escape(basic.get('catId'))}`")
    out.append(f"- method: `{_md_escape(method)}`")
    out.append(f"- path: `{_md_escape(path)}`")
    out.append("")

    out.append("## Request")
    out.append("")

    out.append("### Headers")
    out.append(_render_table(req.get("reqHeaders") or [], [("name", "name"), ("required", "required"), ("desc", "desc"), ("value", "value"), ("example", "example")]).rstrip())
    out.append("")

    out.append("### Query")
    out.append(_render_table(req.get("reqQuery") or [], [("name", "name"), ("required", "required"), ("desc", "desc"), ("example", "example")]).rstrip())
    out.append("")

    out.append("### Path Params")
    out.append(_render_table(req.get("reqParams") or [], [("name", "name"), ("desc", "desc"), ("example", "example")]).rstrip())
    out.append("")

    out.append("### Body")
    out.append("")
    out.append(f"- type: `{_md_escape(req.get('reqBodyType'))}`")

    form_params = req.get("reqBodyForm") or []
    if form_params:
        out.append("")
        out.append(_render_table(form_params, [("name", "name"), ("type", "type"), ("required", "required"), ("desc", "desc"), ("example", "example")]).rstrip())
    body_other = _pretty_json_maybe(req.get("reqBodyOther"))
    if body_other:
        out.append("")
        out.append("```json")
        out.append(body_other)
        out.append("```")
    out.append("")

    out.append("## Response")
    out.append("")
    out.append(f"- type: `{_md_escape(resp.get('resBodyType'))}`")
    out.append(f"- isJsonSchema: `{_md_escape(resp.get('resBodyIsJsonSchema'))}`")
    res_body = _pretty_json_maybe(resp.get("resBody"))
    if res_body:
        out.append("")
        out.append("```json")
        out.append(res_body)
        out.append("```")
    out.append("")

    out.append("## Description")
    out.append("")
    markdown = other.get("markdown") or ""
    if markdown:
        out.append(str(markdown).strip())
    else:
        out.append("_None_")
    out.append("")

    out.append("## Status")
    out.append("")
    out.append(f"`{_md_escape(other.get('status'))}`")
    out.append("")

    return "\n".join(out)


def _project_name_or_fallback(project_id: int, name: Optional[str]) -> str:
    n = (name or "").strip()
    if n:
        return n
    return f"project-{project_id}"


def search_interfaces(
    config: YapiConfig,
    project_name_filter: Optional[str],
    keyword: Optional[str],
    path: Optional[str],
) -> List[Dict[str, Any]]:
    project_name_filter_l = (project_name_filter or "").strip().lower()
    keyword_l = (keyword or "").strip().lower()
    path_l = (path or "").strip().lower()

    results: List[Dict[str, Any]] = []

    for project_id, token in iter_project_tokens(config):
        project_name: Optional[str] = None
        try:
            project_data = yapi_get_project_by_token(config, token)
            project_name = str(project_data.get("name") or "").strip() or None
        except Exception:
            # Do not interrupt search due to project name retrieval failure
            project_name = None

        resolved_project_name = _project_name_or_fallback(project_id, project_name)
        if project_name_filter_l and project_name_filter_l not in resolved_project_name.lower():
            continue

        page_size = max(1, int(config.search_page_size))
        max_pages = max(1, int(config.search_max_pages))

        for page in range(1, max_pages + 1):
            data = yapi_list_interfaces_raw(config, project_id, page, page_size)
            items = data.get("list") if isinstance(data, dict) else None
            if not isinstance(items, list) or not items:
                break

            for it in items:
                if not isinstance(it, dict):
                    continue

                title = str(it.get("title") or "")
                pth = str(it.get("path") or "")
                if keyword_l and keyword_l not in title.lower():
                    continue
                if path_l and path_l not in pth.lower():
                    continue

                results.append(
                    {
                        "projectId": project_id,
                        "projectName": resolved_project_name,
                        "interfaceId": it.get("_id"),
                        "title": it.get("title"),
                        "path": it.get("path"),
                        "method": it.get("method"),
                        "catid": it.get("catid"),
                        "status": it.get("status"),
                    }
                )

            total = data.get("total") if isinstance(data, dict) else None
            try:
                total_i = int(total) if total is not None else 0
            except Exception:
                total_i = 0
            if total_i and page * page_size >= total_i:
                break

    results.sort(key=lambda x: (int(x.get("projectId") or 0), int(x.get("interfaceId") or 0)))
    return results


def render_search_results_markdown(items: List[Dict[str, Any]]) -> str:
    if not items:
        return "No matching interfaces found.\n"

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        pname = str(it.get("projectName") or "unknown")
        grouped.setdefault(pname, []).append(it)

    out: List[str] = []
    for project_name in sorted(grouped.keys()):
        out.append(f"## {_md_escape(project_name)}")
        out.append("")
        rows = grouped[project_name]
        rows.sort(key=lambda x: int(x.get("interfaceId") or 0))
        for r in rows:
            out.append(
                f"- `{_md_escape(r.get('interfaceId'))}` "
                f"`{_md_escape(r.get('method'))}` "
                f"`{_md_escape(r.get('path'))}` - "
                f"{_md_escape(r.get('title'))}"
            )
        out.append("")
    return "\n".join(out)
