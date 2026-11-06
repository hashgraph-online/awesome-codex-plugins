#!/usr/bin/env python3
"""Append one timestamped line per tool hook event, for harnesses whose logs carry no per-call timing.

Wire it as the harness's pre-tool and post-tool hook (references/ADAPTERS.md § Capturing with hooks):

    hook_capture.py pre  --agent <agent> [--harness <surface>]
    hook_capture.py post --agent <agent> [--harness <surface>]

The hook payload is read from stdin as JSON; field names vary by harness, so several spellings are
tried. The script never blocks the tool: it prints nothing, swallows every error, and exits 0.
Lines go to $AGENT_LATENCY_HOOK_LOG, default ~/.cache/agent-tool-call-latency/hooks.jsonl.
"""
import json
import os
import sys
import time

KEYS = {
    "id": ("tool_use_id", "toolUseId", "tool_call_id", "toolCallId", "call_id", "callId"),
    "tool": ("tool_name", "toolName", "tool", "name"),
    "session": ("session_id", "sessionId", "conversation_id", "conversationId", "thread_id", "threadId"),
    "input": ("tool_input", "toolInput", "input", "arguments", "args", "parameters"),
    "cwd": ("cwd", "workspace", "workspace_root", "project_dir"),
}


def pick(payload, field):
    for key in KEYS[field]:
        if payload.get(key) not in (None, ""):
            return payload[key]
    return None


def failed(payload):
    """Claude Code puts a failed result under tool_response; other harnesses report it at the top."""
    response = payload.get("tool_response") or payload.get("toolResponse")
    nested = response if isinstance(response, dict) else {}
    return bool(payload.get("error") or payload.get("is_error") or nested.get("error") or nested.get("is_error"))


def main():
    t = int(time.time() * 1000)
    event = sys.argv[1] if len(sys.argv) > 1 else "?"
    opts = dict(zip(sys.argv[2::2], sys.argv[3::2]))
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    tool = pick(payload, "tool")
    if isinstance(tool, dict):
        tool = tool.get("name")
    inp = pick(payload, "input")
    if isinstance(inp, str):
        try:
            inp = json.loads(inp)
        except ValueError:
            inp = {"command": inp}
    command = inp.get("command") or inp.get("cmd") if isinstance(inp, dict) else None
    if isinstance(command, list):
        command = " ".join(map(str, command))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from common import COMMAND_MAX, clip

    line = {"t": t, "event": event, "agent": opts.get("--agent", "unknown"), "harness": opts.get("--harness"),
            "session": pick(payload, "session"), "id": pick(payload, "id"), "tool": tool,
            "cwd": str(pick(payload, "cwd") or os.getcwd()),
            "command": clip(command, COMMAND_MAX) if command else None,
            "error": failed(payload)}
    path = os.environ.get("AGENT_LATENCY_HOOK_LOG") or os.path.expanduser("~/.cache/agent-tool-call-latency/hooks.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps({k: v for k, v in line.items() if v is not None}) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
