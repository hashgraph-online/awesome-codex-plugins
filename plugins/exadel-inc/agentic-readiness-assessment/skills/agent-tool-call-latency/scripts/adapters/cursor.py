"""Cursor IDE agent: tool-call bubbles in globalStorage/state.vscdb (table cursorDiskKV).

Each tool call is one `bubbleId:<composerId>:<bubbleId>` row whose JSON carries `toolFormerData`
(name, params, status, toolCallId) and the call's own `startedAtMs` / `completedAtMs` (exact).
A call that waited for the user's review (an edit outside the workspace, a command needing
approval) has `toolFormerData.additionalData.reviewData`.
"""
import json
import os

from common import guess_kind, query_ro, record

NAME = "cursor"
AGENT = "Cursor"
KINDS = {"run_terminal_command_v2": "shell", "run_terminal_cmd": "shell", "read_file_v2": "read", "read_file": "read",
         "read_lints": "read", "edit_file_v2": "edit", "edit_file": "edit", "search_replace": "edit", "write": "edit",
         "delete_file": "edit", "ripgrep_raw_search": "search", "grep_search": "search", "glob_file_search": "search",
         "list_dir": "search", "codebase_search": "search", "web_search": "web", "await": "wait",
         "ask_question": "ask_user", "task_v2": "subagent", "todo_write": "other", "update_current_step": "other",
         "get_mcp_tools": "other", "search_conversations": "other", "set_active_branch": "other"}


def _db(ctx):
    return ctx.path("Library", "Application Support", "Cursor", "User", "globalStorage", "state.vscdb")


def detect(ctx):
    return [_db(ctx)] if os.path.exists(_db(ctx)) else []


def records(ctx):
    path = _db(ctx)
    if not os.path.exists(path):
        return
    rows = query_ro(
        path,
        "select key, value from cursorDiskKV where key like 'bubbleId:%' and json_valid(value) "
        "and json_extract(value, '$.toolFormerData.name') is not null "
        "and json_extract(value, '$.startedAtMs') >= ? and json_extract(value, '$.completedAtMs') is not null",
        (int(ctx.since),))
    for key, value in rows:
        yield from _call(ctx, path, key, json.loads(value))


def _call(ctx, path, key, b):
    t = b["toolFormerData"]
    extra = t.get("additionalData") if isinstance(t.get("additionalData"), dict) else {}
    try:
        params = json.loads(t.get("params") or "{}")
    except ValueError:
        params = {}
    params = params if isinstance(params, dict) else {}
    name = t.get("name") or "?"
    kind = KINDS.get(name) or ("mcp" if name.startswith("mcp-") else guess_kind(name))
    paths = (params.get("requestedSandboxPolicy") or {}).get("additionalReadwritePaths") or []
    cwd = params.get("cwd") or (paths[0] if paths else "")
    if ctx.excluded(cwd):
        return
    fields = dict(agent=AGENT, harness="Cursor", session=key.split(":")[1], id=t.get("toolCallId") or b.get("bubbleId"),
                  ts=b["startedAtMs"], dur_ms=max(0, b["completedAtMs"] - b["startedAtMs"]), tool=name, kind=kind,
                  error=t.get("status") not in ("completed", None) or extra.get("status") == "error",
                  human_wait="reviewData" in extra, timing="exact", project=os.path.basename(cwd.rstrip("/")) or None,
                  src=f"{path}:{key}", _cwd=cwd)
    if kind == "shell":
        fields["command"] = params.get("command") or ""
    elif kind == "mcp":
        server, _, tool = name[len("mcp-"):].rpartition("-")
        fields.update(mcp_server=server or name, mcp_tool=tool)
    if extra.get("blockReason"):
        fields["approval"] = str(extra["blockReason"])
    yield record(**fields)
