"""Codex rollouts: ~/.codex/sessions/YYYY/MM/DD/*.jsonl and ~/.codex/archived_sessions/*.jsonl.

`item_completed` events carry the harness's own start and end (exact). Other function calls are
paired from `function_call` / `function_call_output` line timestamps (derived). Approval-reviewer
("guardian") sessions are separate rollouts; each reviewer turn becomes one `review` call.
"""
import glob
import os

from common import each_source, guess_kind, iso_ms, read_jsonl, record

NAME = "codex"
AGENT = "Codex"
# Covered by item_completed with exact timing; their function_call pairs would double-count.
ITEM_COVERED = {"exec_command", "apply_patch", "shell", "js", "sleep"}
FN_KIND = {"wait": "wait", "wait_agent": "wait", "clock.sleep": "wait", "spawn_agent": "subagent",
           "request_user_input": "ask_user", "request_user_input_async": "ask_user", "view_image": "read"}


def harness_for(originator):
    if originator in ("T3 Code", "t3code_desktop"):
        return "T3 Code → Codex"
    if originator == "Codex Desktop":
        return "Codex Desktop"
    if originator == "Claude Code":
        return "Codex via Claude Code plugin"
    return f"Codex CLI ({originator})"


def _files(ctx):
    found = glob.glob(ctx.path(".codex", "sessions", "**", "*.jsonl"), recursive=True)
    found += glob.glob(ctx.path(".codex", "archived_sessions", "*.jsonl"))
    return [f for f in found if os.path.getmtime(f) * 1000 >= ctx.since]


def detect(ctx):
    return _files(ctx)


def records(ctx):
    return each_source(NAME, _files(ctx), lambda path: _rollout(ctx, path))


def _rollout(ctx, path):
    originator, sid, cwd, guardian, sub = None, None, "", False, False
    fn_start, sub_start = {}, {}
    for n, d in read_jsonl(path):
        p = d.get("payload")
        if not isinstance(p, dict):
            continue
        if d.get("type") == "session_meta":
            originator, sid, cwd = p.get("originator"), p.get("id"), p.get("cwd") or ""
            # `source.subagent` is a dict for spawned agents and the reviewer, and a plain string
            # such as "review" for a /review session.
            src = p.get("source")
            spawned = src.get("subagent") if isinstance(src, dict) else None
            guardian = isinstance(spawned, dict) and spawned.get("other") == "guardian"
            sub = spawned is not None and not guardian
            continue
        if ctx.excluded(cwd):
            return
        base = dict(agent=AGENT, harness=harness_for(originator), session=sid or os.path.basename(path),
                    subagent=sub, project=os.path.basename(cwd), src=f"{path}:{n}", _cwd=cwd)
        t = p.get("type")
        if guardian:
            if t == "task_complete" and p.get("duration_ms") is not None and p.get("started_at") is not None:
                start = p["started_at"] * 1000
                if start >= ctx.since:
                    yield record(**base, id=f"review:{sid}:{p.get('turn_id')}", ts=start, dur_ms=p["duration_ms"],
                                 tool="auto_review", kind="review", detail="approval reviewer turn", timing="exact")
            continue
        if t == "item_completed":
            yield from _item(ctx, base, p, sub_start)
        elif t == "function_call":
            start = iso_ms(d.get("timestamp"))
            if start is not None:
                fn_start[p.get("call_id")] = (start, p.get("name") or "?", p.get("namespace"))
        elif t == "function_call_output" and p.get("call_id") in fn_start:
            start, name, ns = fn_start.pop(p["call_id"])
            end = iso_ms(d.get("timestamp"))
            if end is None or start < ctx.since or name in ITEM_COVERED:
                continue
            yield record(**base, id=p["call_id"], ts=start, dur_ms=end - start, tool=name,
                         kind=FN_KIND.get(name) or guess_kind(name), detail=ns, timing="derived")


def _item(ctx, base, p, sub_start):
    it = p.get("item") or {}
    start, end = p.get("started_at_ms"), p.get("completed_at_ms")
    if start is None or end is None or start < ctx.since:
        return
    typ = it.get("type")
    fields = dict(base, id=it.get("id") or f"{base['session']}:{start}", ts=start, dur_ms=end - start,
                  timing="exact", error=it.get("status") == "failed")
    if typ == "CommandExecution":
        cmd = it.get("command")
        fields.update(tool="exec_command", kind="shell", command=cmd[-1] if isinstance(cmd, list) else (cmd or ""),
                      error=it.get("exit_code") not in (0, None) or it.get("status") == "failed")
    elif typ == "McpToolCall":
        fields.update(tool=f"mcp:{it.get('server')}.{it.get('tool')}", kind="mcp",
                      mcp_server=str(it.get("server")), mcp_tool=str(it.get("tool")))
    elif typ == "FileChange":
        fields.update(tool="apply_patch", kind="edit")
    elif typ == "Extension":
        kind_name = str(it.get("kind") or "extension")
        fields.update(tool=kind_name, kind=FN_KIND.get(kind_name) or ("web" if "search" in kind_name else guess_kind(kind_name)),
                      detail=str(it.get("query") or ""))
    elif typ == "ImageView":
        fields.update(tool="view_image", kind="read")
    elif typ == "CollabAgentToolCall":
        fields.update(tool=it.get("tool") or "collab", kind="subagent")
    elif typ == "SubAgentActivity":
        k = it.get("kind")
        if k == "started":
            sub_start[it.get("agent_thread_id")] = (start, it.get("agent_path"))
        elif k in ("completed", "interrupted") and it.get("agent_thread_id") in sub_start:
            s0, agent_path = sub_start.pop(it.get("agent_thread_id"))
            yield record(**dict(fields, id=f"sub:{it.get('agent_thread_id')}", ts=s0, dur_ms=end - s0,
                                tool="spawn_agent", kind="subagent", detail=agent_path, error=k == "interrupted"))
        return
    else:
        return
    yield record(**fields)
