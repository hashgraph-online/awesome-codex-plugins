#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Convert one OpenAPI operation into a YApi-native payload file.

File-in / file-out by design: give it the spec file path + path + method, it
writes a payload.json that upsertInterface.py consumes. Large schemas flow
through files and never pass through the orchestrating AI's context.

Constraints (KISS / stdlib-only):
- JSON specs only (the standard library has no YAML parser). Convert YAML first.
- Use a fully-dereferenced / "merged" OpenAPI doc (no remaining $ref/allOf),
  e.g. an export's preview-merged.json. Unresolved $ref is passed through as-is.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class YapiConvertError(RuntimeError):
    pass


def _slug(path: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (path or "").lower()).strip("-")
    return s or "interface"


def _merge_parameters(path_level: List[Any], op_level: List[Any]) -> List[Dict[str, Any]]:
    """Merge path-item-level and operation-level OpenAPI parameters.

    Keyed by (in, name); operation-level overrides path-level (per the OpenAPI spec).
    """
    merged: Dict[Tuple[Any, Any], Dict[str, Any]] = {}
    for p in list(path_level) + list(op_level):
        if isinstance(p, dict):
            merged[(p.get("in"), p.get("name"))] = p
    return list(merged.values())


def _params_by_loc(params: List[Any], loc: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in params or []:
        if not isinstance(p, dict) or p.get("in") != loc:
            continue
        sch = p.get("schema")
        schema = sch if isinstance(sch, dict) else {}
        item: Dict[str, Any] = {
            "name": p.get("name"),
            "desc": p.get("description") or "",
        }
        example = p.get("example")
        if example is None:
            example = schema.get("example")
        if example is not None:
            item["example"] = example if isinstance(example, str) else json.dumps(example, ensure_ascii=False)
        if loc in ("query", "header"):
            item["required"] = "1" if p.get("required") else "0"
        out.append(item)
    return out


def _pick_response_schema(operation: Dict[str, Any]) -> Tuple[Optional[Any], Optional[str]]:
    """Pick the success (2xx) JSON response schema. Returns (schema, warning)."""
    responses = operation.get("responses") or {}
    key: Optional[str] = "200" if "200" in responses else None
    if key is None:
        for k in responses:
            if str(k).startswith("2"):
                key = k
                break
    if key is None:
        return None, None
    content = (responses.get(key) or {}).get("content") or {}
    if not content:
        return None, None  # 2xx without a body (e.g. 204) is fine
    schema = (content.get("application/json") or {}).get("schema")
    if schema is None:
        return None, f"response {key} has no application/json (has: {list(content)}); response body skipped"
    return schema, None


def convert(spec: Dict[str, Any], path: str, method: str) -> Tuple[Dict[str, Any], Optional[str], List[str]]:
    method_l = method.lower()
    paths = spec.get("paths") or {}
    if path not in paths:
        raise YapiConvertError(f"path not found in spec: {path}")
    item = paths.get(path) or {}
    if method_l not in item:
        have = [m for m in item if m in ("get", "post", "put", "delete", "patch", "head", "options")]
        raise YapiConvertError(f"method {method.upper()} not found for path {path} (have: {have})")
    op = item.get(method_l) or {}
    warnings: List[str] = []

    # operation-level 参数覆盖 path-item-level（OpenAPI 标准）
    params = _merge_parameters(item.get("parameters") or [], op.get("parameters") or [])
    payload: Dict[str, Any] = {
        "title": op.get("summary") or op.get("operationId") or f"{method.upper()} {path}",
        "path": path,
        "method": method.upper(),
        "markdown": op.get("description") or "",
    }
    for loc, field in (("query", "req_query"), ("path", "req_params"), ("header", "req_headers")):
        vals = _params_by_loc(params, loc)
        if vals:
            payload[field] = vals

    rb_content = ((op.get("requestBody") or {}).get("content")) or {}
    if rb_content and "application/json" not in rb_content:
        warnings.append(f"requestBody has no application/json (has: {list(rb_content)}); request body skipped")
    rb_schema = (rb_content.get("application/json") or {}).get("schema")
    if rb_schema is not None:
        payload["req_body_type"] = "json"
        payload["req_body_is_json_schema"] = True
        payload["req_body_other"] = json.dumps(rb_schema, ensure_ascii=False)

    res_schema, res_note = _pick_response_schema(op)
    if res_note:
        warnings.append(res_note)
    if res_schema is not None:
        payload["res_body_type"] = "json"
        payload["res_body_is_json_schema"] = True
        payload["res_body"] = json.dumps(res_schema, ensure_ascii=False)

    tags = op.get("tags") or []
    tag = tags[0] if tags else None
    return payload, tag, warnings


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Convert one OpenAPI operation to a YApi-native payload file (JSON spec only; use a dereferenced/merged doc)."
    )
    ap.add_argument("--spec", required=True, help="Path to a JSON OpenAPI doc (dereferenced/merged)")
    ap.add_argument("--path", required=True, help="OpenAPI path, e.g. /admin/ad/campaign/create")
    ap.add_argument("--method", required=True, help="HTTP method, e.g. post")
    ap.add_argument("--out", default=None, help="Payload output path (default: ./.yapi-sync/payload-...json)")
    args = ap.parse_args(argv)

    try:
        spec_path = Path(args.spec).expanduser()
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        except FileNotFoundError as e:
            raise YapiConvertError(f"Spec not found: {spec_path}") from e
        except json.JSONDecodeError as e:
            raise YapiConvertError(f"Spec is not valid JSON (only JSON specs supported; convert YAML first): {e}") from e
        if not isinstance(spec, dict):
            raise YapiConvertError("Spec root must be a JSON object")

        payload, tag, warnings = convert(spec, args.path, args.method)

        out_path = (
            Path(args.out).expanduser()
            if args.out
            else Path.cwd() / ".yapi-sync" / f"payload-{args.method.lower()}-{_slug(args.path)}.json"
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # 精简摘要（不打印完整 schema，避免灌入上下文）
        print(f"converted {args.method.upper()} {args.path}")
        print(f"  title: {payload['title']}")
        print(f"  tag (-> --category): {tag}")
        fields: List[str] = []
        for field, label in (("req_query", "query"), ("req_params", "path"), ("req_headers", "header")):
            if payload.get(field):
                fields.append(f"{label}x{len(payload[field])}")
        if payload.get("req_body_other"):
            fields.append("reqBody(json-schema)")
        if payload.get("res_body"):
            fields.append("resBody(json-schema)")
        if payload.get("markdown"):
            fields.append(f"markdown({len(payload['markdown'])}c)")
        print(f"  fields: {', '.join(fields) or 'none'}")
        print(f"  payload: {out_path}")
        hint_cat = f" --category {shlex.quote(tag)}" if tag else ""
        print(f"  next: python3 upsertInterface.py --projectId <id> --payload {shlex.quote(str(out_path))}{hint_cat}")

        for w in warnings:
            print(f"  WARN: {w}", file=sys.stderr)
        return 0
    except YapiConvertError as e:
        print(str(e), file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"Unknown error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
