#!/usr/bin/env python3
"""PreToolUse hook: the host asks the user before Digital Marketing Pro prepares, approves or fires a live write.

A live write is three shell commands the model runs itself: `connector_executor.py --execute` (prepare),
`approval-manager.py --action approve` (or `create-standing`), then `connector_executor.py --execute
--approval-id X` (fire). The approval record proves those steps ran in order; only the host's permission prompt
shows them to a person. An allow rule (a skill's `allowed-tools`, or a "Yes, and don't ask again" saved for the
executor's path) would skip that prompt, so this hook answers "ask" for those commands, which makes Claude Code
prompt even when an allow rule matches.

hooks.json runs it only when the command names one of the two scripts (`if` filters), so it adds nothing to any
other shell command. It is a string check: no model call, no network, no file access. Stdlib only.

Limits, stated plainly: it reads the command text. A command that reaches the scripts without naming them (a glob
such as `connector_exec*.py`, a wrapper script) is not seen. Hosts other than Claude Code may not run plugin
hooks at all; there the typed `yes` in each skill and the host's own prompt are what remain.
"""
from __future__ import annotations

import json
import re
import sys

APPROVAL_SCRIPT = re.compile(r"approval[-_]manager(?:\.py)?\b", re.I)
EXECUTOR_SCRIPT = re.compile(r"connector[-_]executor(?:\.py)?\b", re.I)
# approve / create-standing as a whole word: `--action approve`, `--action=approve`, `--action "approve"`.
APPROVAL_ACTIONS = re.compile(r"(?<![\w-])(approve|create-standing)(?![\w-])")
# --execute, --approval-id and --prepare-batch, plus any shortened `--e…` / `--approval…` / `--prep…` spelling
# (the scripts refuse abbreviations since 3.42.0; the hook does not rely on that).
EXECUTOR_LIVE_FLAGS = re.compile(r"(?<![\w-])--(?:e[\w-]*|approval[\w-]*|prep[\w-]*)")

REASON_APPROVE = ("Digital Marketing Pro: this records an approval for a live write (post, email, CRM, ads). "
                  "Allow it only if you asked for this exact action.")
REASON_FIRE = ("Digital Marketing Pro: this prepares or sends a live write through a connector (post, email, CRM, "
               "ads). Allow it only if you asked for this exact action.")


def command_of(raw: str) -> str:
    """The shell command in a PreToolUse payload. Unreadable input falls back to the raw text, so a payload the
    hook cannot parse is still checked rather than waved through."""
    try:
        payload = json.loads(raw)
    except ValueError:
        return raw
    if not isinstance(payload, dict):
        return raw
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]
    return raw


def reason_to_ask(command: str) -> str | None:
    """Why the host must ask before this command runs, or None when it is not a live-write step."""
    if APPROVAL_SCRIPT.search(command) and APPROVAL_ACTIONS.search(command):
        return REASON_APPROVE
    if EXECUTOR_SCRIPT.search(command) and EXECUTOR_LIVE_FLAGS.search(command):
        return REASON_FIRE
    return None


def decision(reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "ask",
                                   "permissionDecisionReason": reason}}


def main() -> int:
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        return 0
    reason = reason_to_ask(command_of(raw))
    if reason:
        sys.stdout.write(json.dumps(decision(reason)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
