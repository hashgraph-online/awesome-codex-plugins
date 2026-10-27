"""Claude Code transcripts: ~/.claude/projects/<project>/<session>.jsonl (subagents under /subagents/).

A tool_use block and its tool_result arrive as separate lines, each with an ISO timestamp.
"""
import glob
import json
import os

from common import each_source, iso_ms, read_jsonl, record

NAME = "claude-code"
AGENT = "Claude Code"
HARNESS_BY_ENTRYPOINT = {"cli": "Claude Code CLI", "claude-desktop": "Claude Desktop", "sdk-cli": "claude -p",
                         "sdk-ts": "Agent SDK app", "sdk-py": "Agent SDK app"}
KIND_BY_TOOL = {"Bash": "shell", "Read": "read", "Grep": "search", "Glob": "search", "LS": "search",
                "Edit": "edit", "Write": "edit", "MultiEdit": "edit", "NotebookEdit": "edit",
                "WebFetch": "web", "WebSearch": "web", "Agent": "subagent", "Task": "subagent",
                "Workflow": "subagent", "Monitor": "wait", "ScheduleWakeup": "wait", "BashOutput": "wait",
                "TaskOutput": "wait", "AskUserQuestion": "ask_user"}


def _files(ctx):
    return [f for f in glob.glob(ctx.path(".claude", "projects", "**", "*.jsonl"), recursive=True)
            if os.path.getmtime(f) * 1000 >= ctx.since]


def detect(ctx):
    return _files(ctx)


def records(ctx):
    return each_source(NAME, _files(ctx), lambda path: _session(ctx, path))


def _session(ctx, path):
    uses, results, msg_end = {}, [], {}
    entry = sid = None
    cwd, mode = "", None
    for n, d in read_jsonl(path):
        entry = entry or d.get("entrypoint")
        sid = sid or d.get("sessionId")
        cwd = cwd or d.get("cwd") or ""
        if d.get("permissionMode"):
            mode = d["permissionMode"]
        msg, ts = d.get("message"), d.get("timestamp")
        t = iso_ms(ts)
        if t is None or not isinstance(msg, dict) or not isinstance(msg.get("content"), list):
            continue
        if d.get("type") == "assistant" and msg.get("id"):
            msg_end[msg["id"]] = max(msg_end.get(msg["id"], 0), t)
        for b in msg["content"]:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use" and b.get("id"):
                uses[b["id"]] = (t, b.get("name") or "?", b.get("input") or {}, mode, d.get("version"), msg.get("id"))
            elif b.get("type") == "tool_result" and b.get("tool_use_id") in uses:
                results.append((b["tool_use_id"], t, b.get("is_error"), d.get("permissionDecision"), n))
    if ctx.excluded(cwd):
        return
    harness = HARNESS_BY_ENTRYPOINT.get(entry, f"Claude Code ({entry})")
    for tid, t_end, is_err, decision, line in results:
        t_start, name, inp, mode, version, mid = uses[tid]
        if t_start < ctx.since:
            continue
        # Parallel calls share one assistant message, and most start only once its last block has
        # streamed, so timing from the call's own block would count generation as tool time.
        # Read-only tools may start mid-stream and return before the message ends; those keep
        # their own block as the start.
        end_of_msg = msg_end.get(mid, 0)
        start = max(t_start, end_of_msg) if t_end >= end_of_msg else t_start
        dur = t_end - start
        if dur < 0:
            continue
        inp = inp if isinstance(inp, dict) else {}
        decision = decision if isinstance(decision, dict) else {}
        fields = dict(agent=AGENT, harness=harness, session=sid or os.path.basename(path), id=tid, ts=start,
                      dur_ms=dur, tool=name, kind=KIND_BY_TOOL.get(name, "other"), error=bool(is_err),
                      background=bool(inp.get("run_in_background")),
                      human_wait=str(decision.get("source", "")).startswith("user"),
                      subagent="/subagents/" in path, mode=mode, version=str(version) if version else None,
                      approval=decision.get("reasonType"), timing="derived", project=os.path.basename(cwd),
                      src=f"{path}:{line}", _cwd=cwd)
        if name == "Bash":
            fields["command"] = inp.get("command") or ""
        elif name.startswith("mcp__"):
            parts = name.split("__")
            fields.update(kind="mcp", mcp_server=parts[1] if len(parts) > 1 else "?", mcp_tool="__".join(parts[2:]))
        else:
            fields["detail"] = json.dumps(inp)[:160]
        yield record(**fields)
