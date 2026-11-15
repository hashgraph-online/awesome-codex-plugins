"""R48 - Coding-agent hooks: Claude Code and Codex call the agent_bridge CLI.

The hooks below are the documented shapes (verified 2026-11-15, see
agent_bridge/hooks.py). This recipe runs each hook command in-process with a
sample hook payload on stdin and checks what the coding agent gets back.

Run:  py -3 examples/python/recipes/r48_coding_agent_hooks.py
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys

import _common as c
from agent_bridge import cli
from agent_bridge.transport import DryRunTransport

BRIDGE = "py -3 \"$SKILL/examples/python/agent_bridge\""      # $SKILL: where this skill is installed

CLAUDE_SETTINGS = {"hooks": {
    "Notification": [{"matcher": "permission_prompt|idle_prompt",
                      "hooks": [{"type": "command", "command": f"{BRIDGE} --live hook claude-notification"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": f"{BRIDGE} --live hook claude-stop"}]}],
    "PermissionRequest": [{"matcher": "Bash",
                           "hooks": [{"type": "command", "timeout": 300,
                                      "command": f"{BRIDGE} --live --state \"$HOME/.agent_bridge/state.json\" "
                                                 "hook claude-permission --ttl 240"}]}],
}}
CODEX_HOOKS = {"hooks": {
    "Stop": [{"hooks": [{"type": "command", "command": f"{BRIDGE} --live hook codex-stop"}]}],
    "PermissionRequest": [{"matcher": "Bash", "hooks": [{"type": "command",
                                                         "command": f"{BRIDGE} --live hook codex-permission --ttl 240"}]}],
}}

PAYLOADS = {
    "claude-notification": {"session_id": "abc123", "cwd": "/work/shop-api", "hook_event_name": "Notification",
                            "title": "Permission needed", "message": "Claude needs your permission to use Bash",
                            "notification_type": "permission_prompt"},
    "claude-stop": {"session_id": "abc123", "cwd": "/work/shop-api", "hook_event_name": "Stop",
                    "stop_hook_active": False, "background_tasks": [],
                    "last_assistant_message": "Refactored the cart service; 42 tests pass. PR description drafted."},
    "claude-permission": {"session_id": "abc123", "cwd": "/work/shop-api", "hook_event_name": "PermissionRequest",
                          "tool_name": "Bash", "tool_input": {"command": "npm run db:migrate -- --env=staging",
                                                              "description": "Apply 2 migrations to staging"}},
    "codex-stop": {"session_id": "s-77", "cwd": "/work/shop-api", "hook_event_name": "Stop", "turn_id": "t-9",
                   "stop_hook_active": False, "last_assistant_message": "Done: lint fixed in 6 files."},
}
ENV = {"AGENT_BRIDGE_OPERATOR_ID": "111111111"}


def invoke(kind: str, *extra: str, fixture: str | None = None):
    t = DryRunTransport()
    argv = ["--quiet", "hook", kind, *extra]
    if fixture:
        argv[1:1] = ["--fixture", os.path.join(c.ROOT, "fixtures", fixture)]
    out, old = io.StringIO(), sys.stdin
    sys.stdin = io.StringIO(json.dumps(PAYLOADS.get(kind, {})))
    try:
        with contextlib.redirect_stdout(out):
            code = cli.run(argv, environ=ENV, transport=t)
    finally:
        sys.stdin = old
    return code, out.getvalue(), t


def run():
    results = {k: invoke(k) for k in ("claude-notification", "claude-stop", "codex-stop")}
    results["claude-permission"] = invoke("claude-permission", fixture="agent_approve_tap.json")
    results["codex-permission-reject"] = invoke("codex-permission", fixture="agent_reject_tap.json")
    results["claude-permission-timeout"] = invoke("claude-permission", "--ttl", "60")
    return results


def main() -> None:
    res = run()
    t = res["claude-permission"][2]
    c.dump(t, "PermissionRequest hook -> Telegram approval")
    code, out, tn = res["claude-notification"]
    c.check(code == 0 and out == "" and "Permission needed — shop-api" in tn.params_of("sendMessage")[0]["text"],
            "Notification: forwarded, nothing on stdout (the hook can't block)")
    code, out, ts = res["claude-stop"]
    c.check(out == "" and ts.params_of("sendMessage")[0].get("disable_notification") is True,
            "Stop: a quiet summary of last_assistant_message; never blocks the stop")
    c.check(json.loads(res["codex-stop"][1]) == {}, "Codex Stop: prints JSON {} (it expects JSON on stdout)")
    c.check(json.loads(res["claude-permission"][1])["hookSpecificOutput"]["decision"] == {"behavior": "allow"},
            "PermissionRequest: Approve in Telegram -> allow")
    c.check(json.loads(res["codex-permission-reject"][1])["hookSpecificOutput"]["decision"]["behavior"] == "deny",
            "Codex PermissionRequest: Reject -> deny (same output shape)")
    c.check(json.loads(res["claude-permission-timeout"][1]) == {},
            "no answer -> no decision -> the normal local prompt (not a silent allow)")
    hook = CLAUDE_SETTINGS["hooks"]["PermissionRequest"][0]["hooks"][0]
    c.check(hook["timeout"] > 240, "the approval TTL (240 s) is below the hook timeout (300 s; default 600)")
    c.check(all("TOKEN" not in json.dumps(x) for x in (CLAUDE_SETTINGS, CODEX_HOOKS)),
            "hook configs name no secrets: the token comes from the environment")


if __name__ == "__main__":
    main()
