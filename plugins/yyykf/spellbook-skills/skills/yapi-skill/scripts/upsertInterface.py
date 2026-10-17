#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Upsert a single YApi interface from a YApi-native payload.

Source-agnostic write primitive:
- Caller supplies a JSON file of YApi-native managed fields (title/path/method/
  req_*/res_body/markdown). Where those fields come from (OpenAPI, changelog,
  hand-written) is the caller's concern, not this script's.
- Read-modify-write: on update, only managed fields are overwritten; everything
  else on the YApi side (mock, test cases, status, ...) is preserved.
- Dry-run by default: writes a preview artifact file + prints a compact summary;
  pass --apply to actually write. Large schemas stay in files, not stdout.
- Create or update is decided by probing YApi (by --interfaceId, else by
  path+method). Never deletes (YApi OpenAPI does not expose delete).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from common import (
    YapiSkillError,
    find_interface_by_path_method,
    load_config,
    yapi_add_cat_raw,
    yapi_add_interface_raw,
    yapi_get_cat_menu_raw,
    yapi_get_interface_detail_raw,
    yapi_up_interface_raw,
)

# 契约管辖、同步时会被覆盖的字段；其余字段属人工内容，更新时不发送、因而保留
MANAGED_FIELDS = [
    "title", "path", "method",
    "req_params", "req_query", "req_headers",
    "req_body_type", "req_body_form", "req_body_other", "req_body_is_json_schema",
    "res_body_type", "res_body", "res_body_is_json_schema",
    "markdown",
]
# 更新时从现有接口回传的"接口定义"字段，防止 up 万一是整体替换语义而清空人工内容；
# 不含 status / 元数据（_id、project_id、uid、add_time...）
WRITABLE_FIELDS = MANAGED_FIELDS + ["catid", "tag", "desc", "api_opened"]


def _slugify(method: str, path: str) -> str:
    raw = f"{method}-{path}".lower()
    s = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return s or "interface"


def _summarize_value(value: Any) -> str:
    if value is None or value == "":
        return "∅"
    if isinstance(value, str):
        return f"{len(value)} chars"
    if isinstance(value, list):
        return f"{len(value)} items"
    if isinstance(value, dict):
        return "object"
    return str(value)


def _json_equal(a: Any, b: Any) -> bool:
    """Structural compare; fields like res_body/req_body_other may be JSON strings."""
    def norm(x: Any) -> Any:
        if isinstance(x, str):
            t = x.strip()
            if t[:1] in ("{", "["):
                try:
                    return json.loads(t)
                except Exception:
                    return x
        return x
    return norm(a) == norm(b)


def compute_diff(existing: Optional[Dict[str, Any]], final: Dict[str, Any]) -> List[Dict[str, Any]]:
    diff: List[Dict[str, Any]] = []
    for f in MANAGED_FIELDS:
        if f not in final:
            continue
        after = final.get(f)
        if existing is None:
            diff.append({"field": f, "change": "set", "after": _summarize_value(after)})
            continue
        before = existing.get(f)
        if not _json_equal(before, after):
            diff.append({
                "field": f,
                "change": "overwrite",
                "before": _summarize_value(before),
                "after": _summarize_value(after),
            })
    return diff


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Upsert one YApi interface from a YApi-native payload (read-modify-write, dry-run by default)."
    )
    parser.add_argument("--projectId", type=int, required=True, help="Target YApi project id")
    parser.add_argument("--payload", type=str, required=True, help="Path to JSON file of YApi-native managed fields")
    parser.add_argument("--interfaceId", type=int, default=None, help="Explicit update target (skips path+method lookup)")
    parser.add_argument("--category", type=str, default=None, help="Category (menu) name for NEW interfaces")
    parser.add_argument("--apply", action="store_true", help="Actually write (default: dry-run)")
    parser.add_argument("--preview-out", type=str, default=None, help="Preview artifact path (default: ./.yapi-sync/...)")
    parser.add_argument("--config", type=str, default=None, help="Config file path (overrides default)")
    args = parser.parse_args(argv)

    try:
        config_path = Path(args.config).expanduser() if args.config else None
        config, _ = load_config(config_path)
        project_id = args.projectId

        payload_path = Path(args.payload).expanduser()
        try:
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
        except FileNotFoundError as e:
            raise YapiSkillError(f"Payload file not found: {payload_path}") from e
        except json.JSONDecodeError as e:
            raise YapiSkillError(f"Payload file is not valid JSON: {payload_path}, {e}") from e
        if not isinstance(payload, dict):
            raise YapiSkillError("Payload must be a JSON object of YApi-native fields")

        # 只接受受管字段，避免调用方混入不该写的字段（如 status）；未知字段记录并提示，不静默吞掉
        managed = {k: v for k, v in payload.items() if k in MANAGED_FIELDS}
        ignored_fields = sorted(k for k in payload if k not in MANAGED_FIELDS)
        path = str(managed.get("path") or "").strip()
        method = str(managed.get("method") or "").strip().upper()

        # 1) 定位目标：显式 id 优先，否则按 (path, method) 探测
        existing: Optional[Dict[str, Any]] = None
        if args.interfaceId is not None:
            existing = yapi_get_interface_detail_raw(config, args.interfaceId, project_id)
        else:
            if not path or not method:
                raise YapiSkillError("Payload must include `path` and `method` (or pass --interfaceId)")
            match = find_interface_by_path_method(config, project_id, path, method)
            if match is not None:
                existing = yapi_get_interface_detail_raw(config, int(match["_id"]), project_id)

        mode = "update" if existing is not None else "create"

        # 2) 分类解析（仅 create 需要；update 保留原分类，不挪位）
        category_info: Dict[str, Any] = {"name": args.category, "catid": None, "willCreate": False}
        if mode == "create":
            cats = yapi_get_cat_menu_raw(config, project_id)
            if args.category:
                cat = next((c for c in cats if str(c.get("name") or "").strip() == args.category.strip()), None)
                if cat is None:
                    category_info["willCreate"] = True
                else:
                    category_info["catid"] = cat.get("_id")
            elif cats:
                cat = cats[0]  # 未指定 -> 落到项目第一个分类（通常“公共分类”）
                category_info = {"name": cat.get("name"), "catid": cat.get("_id"), "willCreate": False}
            else:
                category_info = {"name": "公共分类", "catid": None, "willCreate": True}

        # 3) 构造 final（读-改-写）
        if mode == "update":
            assert existing is not None
            base = {k: existing[k] for k in WRITABLE_FIELDS if k in existing}
            final: Dict[str, Any] = {**base, **managed}
            final["id"] = existing["_id"]
            if "catid" in existing:  # 更新不挪分类
                final["catid"] = existing["catid"]
            final.pop("status", None)
        else:
            final = dict(managed)
            for req in ("title", "path", "method"):
                if not final.get(req):
                    raise YapiSkillError(f"Create requires `{req}` in payload")
            if category_info["catid"] is not None:
                final["catid"] = category_info["catid"]

        # 4) 字段级 diff
        diff = compute_diff(existing, final)

        # 5) 预览产物（完整 payload + diff 落文件，不进 stdout）
        slug = _slugify(method or "x", path or str(args.interfaceId or "interface"))
        preview_path = (
            Path(args.preview_out).expanduser()
            if args.preview_out
            else Path.cwd() / ".yapi-sync" / f"preview-{project_id}-{slug}.json"
        )
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        artifact = {
            "mode": mode,
            "projectId": project_id,
            "method": method,
            "path": path,
            "target": {"interfaceId": existing["_id"] if existing else None},
            "category": category_info,
            "ignoredFields": ignored_fields,
            "diff": diff,
            # 完整 before/after 落盘供人工审阅（stdout 仍只回摘要）
            "existingManaged": {k: existing.get(k) for k in MANAGED_FIELDS if k in existing} if existing else None,
            "finalPayload": final,
        }
        preview_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # 6) stdout 精简摘要
        head = "[apply]" if args.apply else "[dry-run]"
        target_desc = f"interface {existing['_id']}" if existing else "NEW interface"
        print(f"{head} {mode.upper()} {target_desc}  ({method} {path})")
        if mode == "create":
            cat_state = "WILL BE CREATED" if category_info["willCreate"] else "exists"
            print(f"  category: {category_info['name']} ({cat_state}, catid={category_info['catid']})")
        else:
            print(f"  category: kept (catid={final.get('catid')})")
        if diff:
            print("  changes:")
            for d in diff:
                if d["change"] == "set":
                    print(f"    + {d['field']}: {d['after']}")
                else:
                    print(f"    ~ {d['field']}: {d['before']} -> {d['after']}")
        else:
            print("  changes: none (managed fields identical)")
        if ignored_fields:
            print(f"  WARN ignored unknown payload fields: {ignored_fields}")
        print(f"  preview: {preview_path}")

        # 7) apply（默认 dry-run 不写）
        if not args.apply:
            print("  (dry-run; re-run with --apply to write)")
            return 0

        if mode == "create":
            if category_info["catid"] is None:
                created = yapi_add_cat_raw(config, project_id, str(category_info["name"] or "公共分类"))
                new_catid = created.get("_id") if isinstance(created, dict) else None
                if not new_catid:
                    raise YapiSkillError(f"Failed to create category: {category_info['name']}")
                final["catid"] = new_catid
                print(f"  created category {category_info['name']} (catid={new_catid})")
            result = yapi_add_interface_raw(config, project_id, final)
            new_id = result.get("_id") if isinstance(result, dict) else None
            print(f"  ✓ created interface id={new_id}")
        else:
            assert existing is not None
            yapi_up_interface_raw(config, project_id, final)
            print(f"  ✓ updated interface id={existing['_id']}")
        return 0

    except YapiSkillError as e:
        print(str(e), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Cancelled", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unknown error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
