"""The call record every adapter emits, and helpers adapters share.

The record format is specified in references/SCHEMA.md; change both together.
"""
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone

KINDS = {"shell", "read", "search", "edit", "web", "mcp", "subagent", "wait", "review", "ask_user", "other"}
TIMINGS = {"exact", "derived", "inferred"}
REQUIRED = {"agent": str, "harness": str, "session": str, "id": str, "ts": (int, float),
            "dur_ms": (int, float), "tool": str, "kind": str}
OPTIONAL = {"command": str, "mcp_server": str, "mcp_tool": str, "detail": str, "project": str,
            "error": bool, "background": bool, "human_wait": bool, "subagent": bool,
            "mode": str, "version": str, "approval": str, "timing": str, "src": str}

COMMAND_MAX = 2000
DETAIL_MAX = 160

# Token shapes worth masking before a command is written to disk. Commands are kept so the
# auditor can tell `pnpm e2e` from `pnpm test`; credentials in them are never needed.
_SECRET_PATTERNS = [
    (re.compile(r"\b(sk|pk|rk)[-_][A-Za-z0-9_-]{16,}"), "[REDACTED]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "[REDACTED]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "[REDACTED]"),
    (re.compile(r"\bglpat-[A-Za-z0-9_-]{16,}"), "[REDACTED]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "[REDACTED]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[REDACTED]"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"), "[REDACTED]"),
    (re.compile(r"\b(npm|hf)_[A-Za-z0-9]{30,}"), "[REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "[REDACTED]"),
    (re.compile(r"(\b[a-z][a-z0-9+.-]*://[^\s:/@]+:)[^\s@/]+@"), r"\1[REDACTED]@"),
    (re.compile(r"(?i)(authorization:\s*(?:(?:bearer|basic|token)\s+)?)[^\s'\"]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b((?:x-)?[a-z-]*(?:api-key|token|secret)\s*:\s*)[^\s'\"]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(\s--?(?:password|passwd|pass|token|secret|api-key|apikey)(?:=|\s+))(?:\"[^\"]*\"|'[^']*'|\S+)"),
     r"\1[REDACTED]"),
    (re.compile(r"(\s(?:-u|--user)\s+[^\s:]+:)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(\bmysql(?:dump|admin)?\b[^\n;&|]*?\s-p)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|APIKEY|_KEY)[A-Z0-9_]*\s*[=:]\s*)(?:\"[^\"]*\"|'[^']*'|\S+)"),
     r"\1[REDACTED]"),
]


def redact(text):
    if not text:
        return text
    for pat, repl in _SECRET_PATTERNS:
        text = pat.sub(repl, text)
    return text


def clip(text, limit):
    if text is None:
        return None
    text = redact(str(text))
    return text if len(text) <= limit else text[:limit] + "…"


_FRACTION = re.compile(r"\.(\d+)")


def iso_ms(value):
    """Epoch milliseconds from an ISO-8601 string (a trailing Z is accepted), or None when the
    value is missing or malformed, so one bad line skips one call instead of the whole run."""
    if not isinstance(value, str):
        return None
    # Python 3.9's fromisoformat accepts only 3- or 6-digit fractions.
    value = _FRACTION.sub(lambda m: "." + m.group(1)[:6].ljust(6, "0"), value.replace("Z", "+00:00"), count=1)
    try:
        return datetime.fromisoformat(value).timestamp() * 1000
    except ValueError:
        return None


def since_ms(day):
    return datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp() * 1000


class Context:
    """What every adapter receives: whose home to read, the window, and which working directories
    to drop (any cwd containing an exclude substring, or, when include substrings are given, any cwd
    containing none of them)."""

    def __init__(self, home, since, exclude_cwd=(), include_cwd=()):
        self.home = home
        self.since = since
        self.exclude_cwd = tuple(exclude_cwd)
        self.include_cwd = tuple(include_cwd)

    def excluded(self, cwd):
        cwd = cwd or ""
        if self.include_cwd and not any(s in cwd for s in self.include_cwd):
            return True
        return any(s in cwd for s in self.exclude_cwd)

    def path(self, *parts):
        return os.path.join(self.home, *parts)


def each_source(adapter, sources, read):
    """Yield read(source) for each source, skipping (with a note on stderr) a source that fails to
    parse, so one corrupt or reformatted file costs its own calls rather than the adapter's."""
    for source in sources:
        try:
            yield from read(source)
        except Exception as err:
            print(f"{adapter}: skipped {source}: {type(err).__name__}: {err}", file=sys.stderr)


def query_ro(path, sql, params=()):
    """Rows of `sql` from a SQLite file opened read-only. When the owning app holds a lock, query
    a temporary copy instead (with its -wal file, which holds the latest writes)."""
    try:
        db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            return db.execute(sql, params).fetchall()
        finally:
            db.close()
    except sqlite3.OperationalError as err:
        if "locked" not in str(err):
            raise
    tmp = tempfile.mkdtemp(prefix="agent-latency-db-")
    try:
        copy = os.path.join(tmp, os.path.basename(path))
        for suffix in ("", "-wal"):
            if os.path.exists(path + suffix):
                shutil.copyfile(path + suffix, copy + suffix)
        db = sqlite3.connect(copy)
        try:
            return db.execute(sql, params).fetchall()
        finally:
            db.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def record(**fields):
    """Build a call record, clipping free text. Raises ValueError on a missing field or unknown kind.

    `_cwd` may be passed for frontend claims during extraction; extract.py strips it before writing.
    """
    for key in REQUIRED:
        if fields.get(key) is None:
            raise ValueError(f"call record missing {key}: {fields.get('id')}")
    if fields["kind"] not in KINDS:
        raise ValueError(f"unknown kind {fields['kind']!r}")
    if fields.get("timing") and fields["timing"] not in TIMINGS:
        raise ValueError(f"unknown timing {fields['timing']!r}")
    fields["id"], fields["session"] = str(fields["id"]), str(fields["session"])
    fields["command"] = clip(fields.get("command"), COMMAND_MAX)
    fields["detail"] = clip(fields.get("detail"), DETAIL_MAX)
    return {k: v for k, v in fields.items() if v is not None}


WRAPPERS = {"env", "time", "sudo", "nohup", "command", "builtin", "lockf", "flock", "timeout", "gtimeout",
            "caffeinate", "nice", "stdbuf"}
SKIP_PREFIX = {"cd", "pushd", "export", "set", "source", ".", "true"}
SUBCOMMAND_TOOLS = {"npx", "bunx", "pnpm", "npm", "bun", "yarn", "uv", "git", "gh", "glab", "docker", "cargo",
                    "go", "make", "python3", "python", "node", "deno", "kubectl"}
VALUE_FLAGS = {"--filter", "-F", "-C", "--dir", "--prefix", "--cwd", "--project", "-p", "-R", "--repo", "-f",
               "--file", "-w", "--workspace"}


def first_cmd(cmd):
    """Leading program of a shell command (with its subcommand for package managers and the like),
    skipping `cd x &&` prefixes, env assignments and wrappers such as `timeout 60` or `lockf file`."""
    if not cmd:
        return "?"
    for seg in re.split(r"&&|\|\||;|\n|\|", cmd):
        toks = seg.strip().split()
        while toks and (re.match(r"^\w+=", toks[0]) or toks[0] in WRAPPERS):
            wrapper, toks = toks[0], toks[1:]
            while toks and toks[0].startswith("-"):
                flag = toks.pop(0)
                if flag in ("-t", "-k", "-s", "-n") and toks:
                    toks.pop(0)
            if wrapper in ("lockf", "flock", "timeout", "gtimeout") and toks:
                toks = toks[1:]
        if not toks or toks[0] in SKIP_PREFIX or toks[0].startswith("#"):
            continue
        prog = os.path.basename(toks[0].strip("'\"(")) or "?"
        if prog in ("python3", "python") and len(toks) > 1 and toks[1] in ("-", "-c", "-I"):
            return f"{prog} <inline>"
        if prog in SUBCOMMAND_TOOLS and len(toks) > 1:
            rest = toks[1:]
            while rest and rest[0].startswith("-"):
                flag = rest.pop(0)
                if flag in VALUE_FLAGS and rest:
                    rest.pop(0)
            sub = rest[0] if rest else ""
            if prog in ("python3", "python", "node", "deno") and sub.endswith((".py", ".js", ".mjs", ".ts")):
                sub = "<script>"
            if prog in ("python3", "python") and sub.startswith("<<"):
                sub = "<inline>"
            return f"{prog} {sub.strip(chr(39) + chr(34))[:24]}".strip()
        return prog[:30]
    return "?"


def read_jsonl(path):
    with open(path, errors="ignore") as fh:
        for n, line in enumerate(fh, 1):
            try:
                yield n, json.loads(line)
            except ValueError:
                continue


_KIND_HINTS = [
    ("mcp", re.compile(r"^mcp[_:.]|__")),
    ("shell", re.compile(r"bash|shell|exec|terminal|run_command|command")),
    ("edit", re.compile(r"edit|write|patch|replace|create_file|insert")),
    ("read", re.compile(r"read|view|cat_file|open_file|image")),
    ("search", re.compile(r"grep|glob|search_files|find|list_dir|^ls$|codebase_search")),
    ("web", re.compile(r"web|fetch|http|browse|url")),
    ("subagent", re.compile(r"agent|task|delegate")),
    ("ask_user", re.compile(r"ask|question|user_input")),
    ("wait", re.compile(r"wait|sleep|poll|monitor")),
]


def guess_kind(tool):
    """Best-effort kind for a tool name from a harness without a known mapping. An adapter that
    knows its harness's tools should map them explicitly instead."""
    name = (tool or "").lower()
    for kind, pat in _KIND_HINTS:
        if pat.search(name):
            return kind
    return "other"
