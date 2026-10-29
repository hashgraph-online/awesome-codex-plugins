#!/usr/bin/env python3
"""``util wakeup-check``: refuse a scheduled wakeup while a phase is running.

The Claude Code plugin's ``PreToolUse`` hook (``hooks/wakeup-check.sh``) runs
this for the ``ScheduleWakeup`` and ``CronCreate`` tools (fix round 26, live
run 11 #2). Claude Code 2.1.293 runs a phase's subagents in the background, so
a headless host ends a turn while they run, and in racing 03 the host called
``ScheduleWakeup`` (1200 s, its prompt re-running ``--generate-tasks … --yes``)
before ending one. The ``claude -p`` process then stayed alive about 16 minutes
after its final result, until the driver killed it; had the wakeup fired, the
phase would have run again. Racing 04 called it mid-run too, and the wakeup's
turn became the run's final message. The subagents' completion notifications
arrive on their own, so a phase never needs one.

**What "a phase is running" means here.** The session's transcript, the one
``report-check.sh`` reads, since the prompt the user last typed
(``report_check.read_turn``: a task notification or a wakeup prompt is not
one): a Bash call that ran the dispatcher with a long-running mode
(``modes.DETACH_MODES``, an alias resolved) started a phase, and the phase is
over once a later tool result printed the next-step block (``[NEXT_COMMAND]``
or ``[WORKFLOW_COMPLETE]`` at a line start, ``report_check.find_blocks``: the
finished phase's own result, ``util next-command``'s at a stop as on a
success, or a read of the phase's log), or that phase call's own result line
ended it (exit ``1`` or ``3``, a failure or a stop before anything ran;
``ask``, which prints no block, on any result line), or, for a call run in the
background, the ``task-notification`` Claude Code sends when that call ended
says it failed or was stopped (fix round 27: a background phase that failed
held every later wakeup of the session). The native write leg's first call
exits ``0`` with ``next`` null and hands its batches to the host, so a result
line or a notification of exit ``0`` alone never says a phase is over. A
subagent's report (an ``Agent``, ``Task`` or ``SendMessage`` result) quoting
the block is the subagent's words, not the phase's output, and ends nothing
(fix round 27). Nor does ``status``: on this host a poll's terminal word can
belong to an earlier run of the same phase folder (SKILL.md's poll loop says
so), and its next-step block, when it prints one, already counts. The
plugin's ``state.json`` is not read: which plan the session works on, and
whether its phase was started by this session or is left over from another,
only the transcript says.

**The transcript is read once it holds the call being decided** (fix round
27). Claude Code writes it in batches, so when the hook starts, the
``ScheduleWakeup`` or ``CronCreate`` call itself, a phase call made in the
same message, and the result of a phase call that just finished can all be
unwritten (measured on 2.1.293 against a localhost stub: on file 0.1 s
later). So :func:`check` waits until the call's own ``tool_use_id`` is on
file and every phase call its message made before it has its result on file
(``report_check.settled_turn``, at most ``report_check.SETTLE_BUDGET_S``):
everything an earlier message did is on file once the call is. A phase call
whose result is still missing then is running, which is what it is when the
two run side by side.

**The user's own wakeups are never refused.** A session that never ran the
dispatcher, a phase that finished, failed or stopped, and anything after a
prompt the user typed all pass. Only a session whose phase has not printed
its next step is refused, and the refusal says what to do instead.

**Advisory, so every error passes.** An unreadable transcript, a bad
argument, a tool this does not watch, a transcript still missing once the
wait ran out: exit 0, no output, and the tool runs. Nothing here touches the
network or writes anything.

**Stdout is the hook's decision channel**, as for ``util report-check``: the
decision is one line starting with :data:`DECISION_PREFIX`, which the hook
script selects from beside the dispatcher's result line.

Import is side-effect free: argparse and all I/O live inside :func:`main`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from . import report_check
    from .stream_bootstrap import bootstrap_streams
except ImportError:  # direct script invocation
    import report_check  # type: ignore
    from stream_bootstrap import bootstrap_streams  # type: ignore

#: The tools that schedule a prompt for later: a self-paced ``/loop`` uses the
#: first, a fixed-interval one and every cron job the second.
SCHEDULING_TOOLS: Tuple[str, ...] = ("ScheduleWakeup", "CronCreate")

#: Every decision line starts with this (Claude Code's ``PreToolUse`` output).
DECISION_PREFIX = '{"hookSpecificOutput"'

#: ``python <…>/multi_llm.py <mode>``: the dispatcher run, its path bare or
#: quoted (a space inside quotes), then the mode word (quotes allowed). A
#: ``grep multi_llm.py …`` or a path read is not a run.
_DISPATCH_RE = re.compile(
    r"\bpython3?\s+(?:\"[^\"]*multi_llm\.py\"|'[^']*multi_llm\.py'|\S*multi_llm\.py)"
    r"\s+[\"']?([A-Za-z][\w-]*)"
)

#: The last ``MULTI_LLM_RESULT: {…}`` line of a tool result.
_RESULT_RE = re.compile(r"^MULTI_LLM_RESULT:\s*(\{.*\})\s*$", re.MULTILINE)

#: The mode whose phase prints no next-step block: its result line ends it.
_NO_BLOCK_MODES = ("ask",)

#: Flags that make a phase call a preview that starts nothing (help, or a dry
#: run that dispatches no subagent), read in the call's own command.
_PREVIEW_FLAGS = ("--help", "-h", "--dry-run", "--dry-run-subagents")

#: Where one chained shell command ends and the next begins.
_COMMAND_END_RE = re.compile(r"&&|\|\||[;|\n]")

#: The ``origin.kind`` of the entry Claude Code sends when a background task
#: ends (``report_check``'s docstring lists the kinds).
_NOTIFICATION_KIND = "task-notification"

#: What a background command's notification says, read off Claude Code
#: 2.1.293 (2026-10-08, a localhost stub): ``<tool-use-id>toolu_…</tool-use-id>``
#: names the call, ``<status>failed</status>`` (``completed`` on exit 0) and
#: ``<summary>Background command "…" failed with exit code 1</summary>``.
_NOTIFIED_CALL_RE = re.compile(r"<tool-use-id>\s*([^<\s]+)\s*</tool-use-id>")
_NOTIFIED_STATUS_RE = re.compile(r"<status>\s*([^<\s]+)\s*</status>")
_NOTIFIED_SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.DOTALL)
_NOTIFIED_EXIT_RE = re.compile(r"exit code (\d+)")
#: The one status that says a call ended well; any other ends its phase.
_NOTIFIED_OK = "completed"


def phase_mode(command: str) -> Optional[str]:
    """The long-running mode a Bash *command* runs the dispatcher with, else
    ``None`` (a ``util`` or ``status`` call, a ``--help`` or dry-run preview,
    or no dispatcher at all). With several calls chained, the last
    long-running one."""
    try:
        from .cli_common import modes_table
    except ImportError:  # direct script invocation
        from cli_common import modes_table  # type: ignore
    modes = modes_table()
    found: Optional[str] = None
    for match in _DISPATCH_RE.finditer(command):
        mode = modes.resolve(match.group(1))
        if mode is None or mode.name not in modes.DETACH_MODES:
            continue
        rest = _COMMAND_END_RE.split(command[match.end():], 1)[0]
        if any(token.strip("\"'") in _PREVIEW_FLAGS for token in rest.split()):
            continue
        found = mode.name
    return found


def _tool_calls(entry: Dict[str, Any]) -> Iterable[Tuple[str, str, Optional[str]]]:
    """``(tool_use_id, tool name, command)`` for each call an assistant entry
    makes; the command is a Bash call's, else ``None``."""
    content = report_check._content(entry)
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "tool_use":
            continue
        name = str(block.get("name") or "")
        tool_input = block.get("input")
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        yield (str(block.get("id") or ""), name,
               command if name == "Bash" and isinstance(command, str) else None)


def _bash_calls(entry: Dict[str, Any]) -> Iterable[Tuple[str, str]]:
    """``(tool_use_id, command)`` for each Bash call an assistant entry makes."""
    for tool_use_id, _name, command in _tool_calls(entry):
        if command is not None:
            yield tool_use_id, command


def _message_id(entry: Dict[str, Any]) -> Optional[str]:
    """The API message an assistant entry belongs to: Claude Code writes one
    entry per content block, each carrying its message's ``id``."""
    message = entry.get("message")
    found = message.get("id") if isinstance(message, dict) else None
    return found if isinstance(found, str) and found else None


def _notified_end(entry: Dict[str, Any]) -> Optional[str]:
    """The call a ``task-notification`` entry says ended badly, else ``None``.

    Only an entry the harness sent (``origin.kind``), never a tool result or a
    prompt quoting one, and only a status other than ``completed`` or an exit
    code other than ``0``: a failed or stopped background phase.
    """
    if entry.get("type") != "user":
        return None
    origin = entry.get("origin")
    if not isinstance(origin, dict) or origin.get("kind") != _NOTIFICATION_KIND:
        return None
    content = report_check._content(entry)
    if isinstance(content, list):
        content = "\n".join(
            part.get("text", "") for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        )
    if not isinstance(content, str):
        return None
    call = _NOTIFIED_CALL_RE.search(content)
    if call is None:
        return None
    status = _NOTIFIED_STATUS_RE.search(content)
    # The summary's last "exit code N": the command's own description, quoted
    # before it, may hold the words too.
    summary = _NOTIFIED_SUMMARY_RE.search(content)
    codes = _NOTIFIED_EXIT_RE.findall(summary.group(1)) if summary else []
    failed = (status is not None and status.group(1) != _NOTIFIED_OK) or (
        bool(codes) and int(codes[-1]) != 0)
    return call.group(1) if failed else None


def _results(entry: Dict[str, Any]) -> Iterable[Tuple[str, str]]:
    """``(tool_use_id, text)`` for each tool result a user entry carries."""
    content = report_check._content(entry)
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "tool_result":
            continue
        inner = block.get("content")
        if isinstance(inner, str):
            text = inner
        elif isinstance(inner, list):
            text = "\n".join(
                part.get("text", "") for part in inner
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )
        else:
            continue
        yield str(block.get("tool_use_id") or ""), text


def _result_exit(text: str) -> Optional[int]:
    """The ``exit`` of the last result line in *text*, else ``None``."""
    matches = _RESULT_RE.findall(text)
    if not matches:
        return None
    try:
        result = json.loads(matches[-1])
    except ValueError:
        return None
    code = result.get("exit") if isinstance(result, dict) else None
    return code if isinstance(code, int) and not isinstance(code, bool) else None


def phase_in_flight(turn: Sequence[Dict[str, Any]]) -> Optional[str]:
    """The mode of the phase still running in *turn*, else ``None``: the
    newest phase call nothing has ended yet."""
    running: Dict[str, str] = {}
    names: Dict[str, str] = {}
    for entry in turn:
        kind = entry.get("type")
        if kind == "assistant":
            for tool_use_id, name, command in _tool_calls(entry):
                names[tool_use_id] = name
                mode = phase_mode(command) if command is not None else None
                if mode is not None:
                    running.pop(tool_use_id, None)
                    running[tool_use_id] = mode
        elif kind == "user":
            ended = _notified_end(entry)
            if ended is not None:
                running.pop(ended, None)
            for tool_use_id, text in _results(entry):
                if names.get(tool_use_id) in report_check.SUBAGENT_TOOLS:
                    continue
                if report_check.find_blocks(text):
                    running.clear()
                    continue
                mode = running.get(tool_use_id)
                if mode is None:
                    continue
                code = _result_exit(text)
                if code in (1, 3) or (code is not None and mode in _NO_BLOCK_MODES):
                    running.pop(tool_use_id)
    return next(reversed(running.values()), None) if running else None


def call_on_file(tool_use_id: str) -> Callable[[List[Dict[str, Any]]], bool]:
    """A ``report_check.settled_turn`` test: the call *tool_use_id* is on
    file, and so is the result of every phase call its message made before
    it (fix round 27)."""

    def settled(turn: List[Dict[str, Any]]) -> bool:
        # The phase calls made before the call, by message: Claude Code
        # writes one entry per content block, each carrying its message's id.
        earlier: List[Tuple[Optional[str], str]] = []
        message: Optional[str] = None
        found = False
        for entry in turn:
            if entry.get("type") != "assistant":
                continue
            for call_id, _name, command in _tool_calls(entry):
                if call_id == tool_use_id:
                    found = True
                    message = _message_id(entry)
                    break
                if command is not None and phase_mode(command) is not None:
                    earlier.append((_message_id(entry), call_id))
            if found:
                break
        if not found:
            return False
        siblings = [call_id for owner, call_id in earlier
                    if message is not None and owner == message]
        if not siblings:
            return True
        answered = {
            call_id
            for entry in turn if entry.get("type") == "user"
            for call_id, _text in _results(entry)
        }
        return all(call_id in answered for call_id in siblings)

    return settled


def deny_reason(tool: str, mode: str) -> str:
    """What the model reads when its scheduling call is refused."""
    return (
        f"multi-llm: {tool} is refused while the {mode} phase you started "
        "has not printed its next step in this session. Do not schedule a "
        "wakeup, a cron job or a loop to come back to it, and never schedule "
        "a phase command to run again: a scheduled prompt keeps a headless "
        "session open after its "
        "last reply, and when it fires the phase runs a second time. Keep "
        "waiting for the phase's subagents (or the dispatcher command you ran "
        "in the background) in this session: each one's completion "
        "notification arrives on its own, and ending your turn while they run "
        "is how you wait. When they are back, carry on with the phase's next "
        "step."
    )


def check(hook: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The hook decision for one tool call: ``None`` to allow, else the deny
    object. Raises ``report_check._Unreadable`` for a transcript it cannot
    read; the caller turns that into an allow."""
    tool = hook.get("tool_name")
    if tool not in SCHEDULING_TOOLS:
        return None
    transcript = hook.get("transcript_path")
    if not isinstance(transcript, str) or not transcript:
        return None
    path = Path(transcript)
    if not path.is_file():
        # hooks/wakeup-check.sh already waited for the file to be written.
        return None
    tool_use_id = hook.get("tool_use_id")
    # Read once the call being decided is on file, or, when the input names
    # no call, once the file stopped growing.
    turn = report_check.settled_turn(
        path,
        call_on_file(tool_use_id)
        if isinstance(tool_use_id, str) and tool_use_id else None,
    )
    mode = phase_in_flight(turn)
    if mode is None:
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": deny_reason(str(tool), mode),
    }}


def build_parser() -> argparse.ArgumentParser:
    parser = report_check._QuietParser(
        prog="multi_llm.py util wakeup-check",
        description=(
            "Refuse a ScheduleWakeup or CronCreate call while a multi-llm phase "
            "this Claude Code session started is still running. Run by the "
            "Claude Code plugin's PreToolUse hook. Prints nothing to allow the "
            'call, and one {"hookSpecificOutput": {…, "permissionDecision": '
            '"deny", …}} line to refuse it. Always exits 0: every error allows.'
        ),
    )
    parser.add_argument(
        "--hook-input",
        metavar="PATH",
        required=True,
        help="The PreToolUse hook's input JSON, as a file or - for stdin. "
             "Supplies tool_name and transcript_path.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    bootstrap_streams()
    parser = build_parser()
    try:
        args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    except report_check._ArgumentError:
        return 0
    try:
        decision = check(report_check._read_hook_input(args.hook_input))
    except Exception:  # noqa: BLE001 - advisory: every failure allows the call
        return 0
    if decision is not None:
        sys.stdout.write(json.dumps(decision) + "\n")
        try:
            sys.stdout.flush()
        except (AttributeError, ValueError):  # pragma: no cover - closed stream
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
