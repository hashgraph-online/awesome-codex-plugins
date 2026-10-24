"""Calls captured live by hook_capture.py: pre and post lines paired by call id, or, when the harness
gives no id, first-in first-out per session and tool."""
import collections
import os

from common import guess_kind, read_jsonl, record

NAME = "hooklog"


def _path():
    return os.environ.get("AGENT_LATENCY_HOOK_LOG") or os.path.expanduser("~/.cache/agent-tool-call-latency/hooks.jsonl")


def detect(ctx):
    return [_path()] if os.path.exists(_path()) else []


def records(ctx):
    if not os.path.exists(_path()):
        return
    by_id, fifo = {}, collections.defaultdict(collections.deque)
    for n, d in read_jsonl(_path()):
        key = (d.get("agent"), d.get("session"), d.get("tool"))
        if d.get("event") == "pre":
            if d.get("id"):
                by_id[(d.get("agent"), d["id"])] = d
            else:
                fifo[key].append(d)
            continue
        if d.get("event") != "post":
            continue
        start = by_id.pop((d.get("agent"), d["id"]), None) if d.get("id") else (fifo[key].popleft() if fifo[key] else None)
        if not start or start["t"] < ctx.since:
            continue
        cwd = start.get("cwd") or ""
        if ctx.excluded(cwd):
            continue
        tool = d.get("tool") or start.get("tool") or "?"
        kind = guess_kind(tool)
        session = d.get("session") or "?"
        server, mcp_tool = _mcp(tool) if kind == "mcp" else (None, None)
        yield record(agent=d.get("agent") or "unknown", harness=d.get("harness") or d.get("agent") or "unknown",
                     session=session, id=d.get("id") or f"{session}:{start['t']}:{tool}", ts=start["t"],
                     dur_ms=d["t"] - start["t"], tool=tool, kind=kind,
                     command=start.get("command") if kind == "shell" else None, mcp_server=server, mcp_tool=mcp_tool,
                     project=os.path.basename(cwd.rstrip("/")) or start.get("project"),
                     error=bool(d.get("error")), timing="exact", src=f"{_path()}:{n}", _cwd=cwd)


def _mcp(tool):
    """Server and tool from the common MCP spellings: `mcp__server__tool` and `mcp:server.tool`."""
    if tool.startswith("mcp__"):
        parts = tool.split("__")
        return (parts[1] if len(parts) > 1 else "?"), "__".join(parts[2:]) or None
    if tool.startswith("mcp:") and "." in tool:
        server, _, name = tool[len("mcp:"):].partition(".")
        return server, name
    return "?", tool
