#!/usr/bin/env python3
"""Pull the user's requests, loose ends and subagent reports out of an agent session transcript (JSONL).

    sweep_transcript.py requests   <transcript.jsonl>   # every message the user typed, numbered
    sweep_transcript.py loose-ends <transcript.jsonl>   # paragraphs from the agent and its subagents that
                                                        # mention unfinished work
    sweep_transcript.py reports    <transcript.jsonl>   # every subagent report, in full

Reads Claude Code transcripts (~/.claude/projects/<slug>/<session>.jsonl) and Codex rollouts
(~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl). For another harness, add a branch to messages().

Nothing is shortened. Each item names the transcript line it came from, and a coverage summary at the end says what
was skipped and why (unreadable lines, records the harness injected, parts this script doesn't cover).
"""
import json
import re
import sys
from collections import Counter

LOOSE_END = re.compile(
    r"out of scope|pre-?existing|follow-?up|\blater\b|not verified|unverified|unconfirmed|not tested|untested"
    r"|skipped|left alone|separate (ticket|issue|story|PR)|worth a ticket|\bTODO\b|\bFIXME\b|\bnit\b"
    r"|open question|product question|limitation|non-finding|suggested (next )?questions?|couldn.t|workaround",
    re.IGNORECASE,
)
# Text the harness itself puts in a user message. Claude Code marks most injected records with isMeta, which is
# checked first; these tags catch the rest. Only text that starts with one of these tags is skipped.
INJECTED_TAGS = (
    "<system-reminder>",
    "<local-command-stdout>",
    "<local-command-stderr>",
    "<local-command-caveat>",
    "<environment_context>",
    "<user_instructions>",
    "<turn_aborted>",
    "# AGENTS.md instructions",
)
SUBAGENT_TOOLS = {"Agent", "Task"}
COMMAND_NAME = re.compile(r"<command-name>(.*?)</command-name>", re.DOTALL)
COMMAND_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.DOTALL)


def texts(content):
    if isinstance(content, str):
        return [content]
    out = []
    for item in content or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") in ("text", "input_text", "output_text"):
            out.append(item.get("text", ""))
        elif item.get("type") == "tool_result":
            out.extend(texts(item.get("content")))
    return out


def user_text(text, skipped):
    """Returns the text the user typed, or None if the harness injected it."""
    stripped = text.strip()
    if stripped.startswith(("<command-name>", "<command-message>")):
        # A slash command the user typed: keep the command and its arguments.
        name, args = COMMAND_NAME.search(stripped), COMMAND_ARGS.search(stripped)
        if name:
            return f"{name.group(1).strip()} {args.group(1).strip() if args else ''}".strip()
        skipped["slash-command records without a command name"] += 1
        return None
    if stripped.startswith(INJECTED_TAGS):
        skipped["injected text (system tags)"] += 1
        return None
    return stripped


def claude_messages(entries, skipped):
    subagent_calls = set()
    for lineno, entry in entries:
        kind = entry.get("type")
        if kind not in ("user", "assistant") or "message" not in entry:
            continue
        if entry.get("isMeta"):
            skipped["records Claude Code marks as meta"] += 1
            continue
        if entry.get("isCompactSummary"):
            skipped["compaction summaries"] += 1
            continue
        if entry.get("isSidechain"):
            # Older Claude Code versions wrote subagent turns inline; their final report also arrives as a tool result.
            skipped["subagent turns (sidechain)"] += 1
            continue
        content = entry["message"].get("content")
        if kind == "assistant":
            for item in content if isinstance(content, list) else []:
                if isinstance(item, dict) and item.get("type") == "tool_use" and item.get("name") in SUBAGENT_TOOLS:
                    subagent_calls.add(item.get("id"))
            for text in texts(content):
                yield lineno, "assistant", text
            continue
        for item in content if isinstance(content, list) else [content]:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                if item.get("tool_use_id") in subagent_calls:
                    for text in texts(item.get("content")):
                        yield lineno, "subagent", text
                continue
            for text in texts([item] if isinstance(item, dict) else item):
                # Background subagents report back as a task notification in a user message.
                if text.lstrip().startswith("<task-notification>"):
                    yield lineno, "subagent", text
                    continue
                typed = user_text(text, skipped)
                if typed is not None:
                    yield lineno, "user", typed


def codex_messages(entries, skipped):
    # Newer Codex versions record each typed message twice: as an event_msg of type user_message, and inside the model
    # input as a response_item (which also carries AGENTS.md, environment context and so on). Older versions, and
    # older turns in a resumed session, have only the response_item. Pair the two copies of one message only when
    # they sit next to each other among the file's messages, with no reply between them, and their text is identical
    # (ignoring only leading and trailing whitespace), and print the event's copy. Everything else is printed, so an
    # earlier request with the same words as a later one is never taken for its duplicate.
    users = []  # (entry index, content index, kind, text) for every user message and reply, in file order
    for index, (_, entry) in enumerate(entries):
        payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
        if entry.get("type") == "event_msg" and payload.get("type") == "user_message":
            users.append((index, 0, "event", str(payload.get("message", ""))))
        elif entry.get("type") == "response_item" and payload.get("type") == "message":
            if payload.get("role") == "assistant":
                # A reply between two user messages means they belong to different turns: never pair across it.
                users.append((index, 0, "assistant", ""))
                continue
            if payload.get("role") != "user":
                continue
            for part, text in enumerate(texts(payload.get("content"))):
                typed = user_text(text, Counter())
                if typed is not None:
                    users.append((index, part, "response", typed))
    duplicates = set()
    i = 0
    while i + 1 < len(users):
        a, b = users[i], users[i + 1]
        if {a[2], b[2]} == {"event", "response"} and a[3].strip() == b[3].strip():
            response = a if a[2] == "response" else b
            duplicates.add((response[0], response[1]))
            i += 2
        else:
            i += 1

    for index, (lineno, entry) in enumerate(entries):
        payload = entry.get("payload") if isinstance(entry.get("payload"), dict) else {}
        if entry.get("type") == "event_msg" and payload.get("type") == "user_message":
            yield lineno, "user", str(payload.get("message", ""))
        elif entry.get("type") == "response_item" and payload.get("type") == "message":
            role = payload.get("role")
            for part, text in enumerate(texts(payload.get("content"))):
                if role == "assistant":
                    yield lineno, "assistant", text
                elif role == "user":
                    typed = user_text(text, skipped)
                    if typed is None:
                        continue
                    if (index, part) in duplicates:
                        skipped["user messages recorded twice, as a response_item and a user_message event (printed once)"] += 1
                        continue
                    yield lineno, "user", typed
        elif entry.get("type") == "compacted":
            skipped["compaction records (the turns before them are still in the file)"] += 1


def read(path):
    entries, bad = [], []
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            # The session being swept is still being written, so its last line can be incomplete.
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                bad.append(lineno)
                continue
            if isinstance(entry, dict):
                entries.append((lineno, entry))
    return entries, bad


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("requests", "loose-ends", "reports"):
        sys.exit(__doc__)
    mode, path = sys.argv[1], sys.argv[2]
    entries, bad = read(path)
    is_codex = any(e.get("type") in ("session_meta", "response_item", "event_msg") for _, e in entries)
    skipped = Counter()
    messages = codex_messages(entries, skipped) if is_codex else claude_messages(entries, skipped)

    n = 0
    for lineno, role, text in messages:
        text = text.strip()
        if not text:
            continue
        if mode == "requests":
            if role == "user":
                n += 1
                print(f"[{n}] (line {lineno}) {text}\n")
        elif mode == "reports":
            if role == "subagent":
                n += 1
                print(f"===== Subagent report {n} (line {lineno}) =====\n{text}\n")
        elif role in ("assistant", "subagent"):
            for paragraph in re.split(r"\n\s*\n", text):
                if LOOSE_END.search(paragraph):
                    n += 1
                    print(f"[{n}] (line {lineno}) {role.upper()}: {paragraph.strip()}\n")

    print("----- Coverage -----")
    print(f"Format: {'Codex' if is_codex else 'Claude Code'}. Records read: {len(entries)}. Items printed: {n}.")
    if bad:
        print(f"Unreadable lines skipped ({len(bad)}): {', '.join(map(str, bad[:20]))}{' ...' if len(bad) > 20 else ''}")
    for reason, count in sorted(skipped.items()):
        print(f"Skipped {count}: {reason}")
    if is_codex and mode in ("reports", "loose-ends"):
        print("Not covered: subagent reports in Codex transcripts. This script doesn't parse them; if the session used")
        print("subagents, read their output in the transcript or the folders they wrote to.")


if __name__ == "__main__":
    main()
