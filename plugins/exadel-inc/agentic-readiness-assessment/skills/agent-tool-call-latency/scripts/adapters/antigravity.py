"""Antigravity (IDE and CLI): one SQLite file per conversation under
~/.gemini/antigravity/conversations/ and ~/.gemini/antigravity-cli/conversations/.

Each row of `steps` holds a protobuf `metadata` blob with no published schema. Read from real
rows on 2026-10-21: field 4 is the tool call (1 = call id, 2 = tool name, 3 = arguments as JSON),
field 6 is when the step started and field 8 when it completed, each a Timestamp (1 = seconds,
2 = nanos), and field 26 lists status changes ({1: status, 2: Timestamp}). Status 3 is done,
4 failed; a step that passes through status 9 sat waiting for the user's approval (a 315 s
`find -maxdepth 1` spent all but 0.1 s there). Steps without field 4 are model or user turns. Re-check these numbers when the
validator warns: an unknown schema can shift between releases.
"""
import glob
import json
import os

from common import each_source, guess_kind, query_ro, record

NAME = "antigravity"
AGENT = "Antigravity"
ROOTS = {"antigravity": "Antigravity", "antigravity-cli": "Antigravity CLI"}
KINDS = {"run_command": "shell", "command_status": "wait", "send_command_input": "shell", "view_file": "read",
         "view_file_outline": "read", "view_code_item": "read", "grep_search": "search", "find_by_name": "search",
         "list_dir": "search", "codebase_search": "search", "write_to_file": "edit", "replace_file_content": "edit",
         "multi_replace_file_content": "edit", "read_url_content": "web", "search_web": "web",
         "browser_subagent": "subagent"}


def _varint(b, i):
    result = shift = 0
    while True:
        c = b[i]
        i += 1
        result |= (c & 0x7F) << shift
        shift += 7
        if c < 0x80:
            return result, i


def _fields(b):
    """Top-level protobuf fields as {number: [value, ...]}; length-delimited values stay bytes."""
    out, i = {}, 0
    while i < len(b):
        key, i = _varint(b, i)
        num, wire = key >> 3, key & 7
        if wire == 0:
            value, i = _varint(b, i)
        elif wire == 2:
            n, i = _varint(b, i)
            value, i = b[i:i + n], i + n
        elif wire == 1:
            value, i = b[i:i + 8], i + 8
        elif wire == 5:
            value, i = b[i:i + 4], i + 4
        else:
            raise ValueError(f"wire type {wire}")
        out.setdefault(num, []).append(value)
    return out


def _ms(blob):
    f = _fields(blob)
    return f.get(1, [0])[0] * 1000 + f.get(2, [0])[0] // 1_000_000


def _dbs(ctx):
    found = []
    for root in ROOTS:
        found += glob.glob(ctx.path(".gemini", root, "conversations", "*.db"))
    return [p for p in found if os.path.getmtime(p) * 1000 >= ctx.since]


def detect(ctx):
    return _dbs(ctx)


def records(ctx):
    return each_source(NAME, _dbs(ctx), lambda path: _conversation(ctx, path))


def _conversation(ctx, path):
    harness = ROOTS[os.path.basename(os.path.dirname(os.path.dirname(path)))]
    rows = query_ro(path, "select idx, status, metadata from steps where metadata is not null")
    session = os.path.splitext(os.path.basename(path))[0]
    for idx, status, meta in rows:
        try:
            m = _fields(meta)
            if 4 not in m or 6 not in m or 8 not in m:
                continue
            call = _fields(m[4][0])
            start, end = _ms(m[6][0]), _ms(m[8][0])
            statuses = [_fields(e).get(1, [0])[0] for e in _fields(m[26][0]).get(1, [])] if 26 in m else []
        except (ValueError, IndexError):
            continue
        if start < ctx.since:
            continue
        name = call.get(2, [b"?"])[0].decode(errors="replace")
        try:
            args = json.loads(call.get(3, [b"{}"])[0].decode(errors="replace"))
        except ValueError:
            args = {}
        args = args if isinstance(args, dict) else {}
        kind = KINDS.get(name) or ("mcp" if name.startswith("mcp_") else guess_kind(name))
        cwd = str(args.get("Cwd") or args.get("cwd") or "")
        if ctx.excluded(cwd):
            continue
        fields = dict(agent=AGENT, harness=harness, session=session,
                      id=call.get(1, [f"{session}:{idx}".encode()])[0].decode(errors="replace"), ts=start,
                      dur_ms=max(0, end - start), tool=name, kind=kind, error=status not in (3,),
                      human_wait=9 in statuses,
                      timing="exact", project=os.path.basename(cwd.rstrip("/")) or None,
                      src=f"{path}:steps.idx={idx}", _cwd=cwd)
        if kind == "shell":
            fields["command"] = str(args.get("CommandLine") or args.get("command") or "")
        elif kind == "mcp":
            fields.update(mcp_server=name.split("_")[1] if "_" in name else name, mcp_tool=name)
        yield record(**fields)
