#!/usr/bin/env python3
"""debt-ops PostToolUse hook: run quality commands in parallel under a 3s budget.

Codex adapter. Codex edits files through the `apply_patch` tool (V4A envelope),
not Claude's Write/Edit, so the changed path isn't `tool_input.file_path` —
we parse the Add/Update/Move-to targets out of the patch instead. We still
honor `file_path` so Edit/Write-shaped tools keep working.
"""

import concurrent.futures
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

MARKER_OPEN = "<!-- debt-ops:feedback v1 -->"
MARKER_CLOSE = "<!-- /debt-ops:feedback -->"
PER_COMMAND_TIMEOUT = 3
SNIPPET_LEN = 200
DEBUG_ENV = "DEBT_OPS_DEBUG"
SKIP_DIRS = {".git", "node_modules", "target", "dist", "build"}
TEST_PATTERNS = (
    re.compile(r"^test_"),
    re.compile(r"_test\."),
    re.compile(r"\.test\."),
    re.compile(r"\.spec\."),
)
HEADING_RE = re.compile(r"^##\s")
# V4A patch envelope: files that exist after the edit (Delete targets are gone).
PATCH_ADD_UPDATE_RE = re.compile(r"^\*\*\* (?:Add|Update) File: (.+?)\s*$")
PATCH_MOVE_RE = re.compile(r"^\*\*\* Move to: (.+?)\s*$")


# Single deterministic cache base so hook subprocesses and skill Bash (which
# never sees PLUGIN_DATA) resolve the same path. Override with DEBT_OPS_CACHE.
def cache_base():
    override = os.environ.get("DEBT_OPS_CACHE")
    return Path(override) if override else (Path.home() / ".cache" / "debt-ops")


# Wraps text in the JSON envelope Codex expects from a PostToolUse hook.
def emit(context):
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": context,
        }
    }
    sys.stdout.write(json.dumps(payload) + "\n")


# Repo root, or None if we're not in a git repo.
def git_toplevel():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        s = out.stdout.strip()
        return Path(s) if s else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


# Short stable hash of the repo path — used as the cache subdirectory name.
def repo_hash(toplevel):
    return hashlib.sha1(str(toplevel).encode()).hexdigest()[:12]


# Pull the V4A patch text out of an apply_patch tool_input. Codex may place it
# in any string field (or hand tool_input as a raw string), so we sniff for the
# envelope markers rather than guessing the field name.
def patch_text(tool_input):
    if isinstance(tool_input, str):
        return tool_input if "*** " in tool_input else ""
    if isinstance(tool_input, dict):
        for v in tool_input.values():
            if isinstance(v, str) and (
                "*** Begin Patch" in v or "*** Update File:" in v or "*** Add File:" in v
            ):
                return v
    return ""


# The just-edited file path(s) from the hook's stdin JSON. Edit/Write expose
# file_path directly; apply_patch carries them inside the patch envelope.
def changed_files_from_stdin():
    try:
        raw = sys.stdin.read()
    except OSError:
        return []
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []
    ti = data.get("tool_input")
    if isinstance(ti, dict):
        fp = ti.get("file_path")
        if isinstance(fp, str) and fp:
            return [fp]
    patch = patch_text(ti)
    if not patch:
        return []
    files = []
    for line in patch.splitlines():
        m = PATCH_ADD_UPDATE_RE.match(line)
        if m:
            files.append(m.group(1))
            continue
        m = PATCH_MOVE_RE.match(line)
        if m:
            # Rename: the new path is what now exists; it supersedes the
            # Update-File source captured on the preceding line.
            if files:
                files[-1] = m.group(1)
            else:
                files.append(m.group(1))
    # De-dup, preserve order.
    seen, out = set(), []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


# Loads quality commands. AGENTS.md marker block wins if present; otherwise the cached list.
def read_commands(toplevel, cache_dir):
    agents_md = toplevel / "AGENTS.md"
    if agents_md.is_file():
        try:
            text = agents_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        if MARKER_OPEN in text:
            block = []
            collecting = False
            for line in text.splitlines():
                if not collecting:
                    if MARKER_OPEN in line:
                        collecting = True
                    continue
                if MARKER_CLOSE in line or HEADING_RE.match(line):
                    break
                block.append(line)
            return "\n".join(block)
    list_file = cache_dir / "feedback.list"
    if list_file.is_file():
        try:
            return list_file.read_text(encoding="utf-8")
        except OSError:
            return ""
    return ""


# Debug log path — only when DEBT_OPS_DEBUG=1 is set in the environment.
def debug_path(cache_dir):
    if not os.environ.get(DEBUG_ENV):
        return None
    return cache_dir / "debug.log"


# Appends one tab-separated line to the debug log; silently no-ops on failure.
def dlog(path, *fields):
    if path is None:
        return
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write("\t".join((ts, *fields)) + "\n")
    except OSError:
        pass


# Runs one quality command under a 3s timeout. Returns (cmd, status, snippet).
def run_one(line, changed_files, env):
    has_var = "$CHANGED_FILES" in line or "${CHANGED_FILES}" in line
    if has_var and not changed_files:
        return line, "SKIP_NO_FILE", ""

    try:
        args = shlex.split(line)
    except ValueError as e:
        return line, "FAIL", f"parse error: {e}"
    if not args:
        return line, "SKIP_NO_FILE", ""

    # Only $CHANGED_FILES is expanded; other shell features (pipes, &&, globs)
    # are not, so we don't need bash on PATH. Wrap in `bash -c '...'` to opt in.
    # A bare $CHANGED_FILES token becomes one argument per file (tools like
    # pytest/eslint need separate argv entries); embedded uses get the joined string.
    if changed_files:
        joined = " ".join(changed_files)
        expanded = []
        for tok in args:
            if tok in ("$CHANGED_FILES", "${CHANGED_FILES}"):
                expanded.extend(changed_files)
            else:
                expanded.append(
                    tok.replace("${CHANGED_FILES}", joined).replace("$CHANGED_FILES", joined)
                )
        args = expanded

    try:
        result = subprocess.run(
            args,
            capture_output=True, text=True,
            timeout=PER_COMMAND_TIMEOUT, env=env,
        )
    except subprocess.TimeoutExpired:
        return line, "TIMEOUT", ""
    except FileNotFoundError:
        return line, "FAIL", f"command not found: {args[0]}"
    except OSError as e:
        return line, "FAIL", str(e)[:SNIPPET_LEN]
    if result.returncode == 0:
        return line, "PASS", ""
    snippet = ((result.stdout or "") + (result.stderr or ""))[:SNIPPET_LEN]
    return line, "FAIL", snippet


# How many .md entries currently live in the (cached or default) registry dir.
def registry_count(toplevel, registry_dir):
    reg = toplevel / registry_dir
    if not reg.is_dir():
        return 0
    try:
        return sum(1 for p in reg.iterdir() if p.is_file() and p.suffix == ".md")
    except OSError:
        return 0


DEFAULT_REGISTRY_DIR = "docs/debt"


# Read session-start.py's cached registry-dir path; default if missing/empty.
def read_registry_dir(cache_dir):
    f = cache_dir / "registry-dir"
    if f.is_file():
        try:
            val = f.read_text(encoding="utf-8").strip()
            if val:
                return val
        except OSError:
            pass
    return DEFAULT_REGISTRY_DIR


# Appends one JSON line to metrics.jsonl in the cache dir; silent no-op on failure.
def log_metric(cache_dir, payload):
    if not cache_dir.is_dir():
        return
    payload["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with (cache_dir / "metrics.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, separators=(",", ":")) + "\n")
    except OSError:
        pass


# Counts test-shaped filenames anywhere in the repo (test_*, *_test.*, *.test.*, *.spec.*).
def test_count(toplevel):
    try:
        n = 0
        for root, dirs, files in os.walk(toplevel):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if any(p.search(f) for p in TEST_PATTERNS):
                    n += 1
        return n
    except OSError:
        return None


def main():
    # Idle out cleanly if we're not in a git repo.
    toplevel = git_toplevel()
    if toplevel is None:
        return 0

    cache_dir = cache_base() / "cache" / repo_hash(toplevel)

    changed_files = changed_files_from_stdin()
    changed = " ".join(changed_files)
    env = os.environ.copy()
    env["CHANGED_FILES"] = changed

    registry_dir = read_registry_dir(cache_dir)

    # One line per edit — the dogfood tripwire signal (edits vs registry growth).
    log_metric(cache_dir, {
        "event": "edit",
        "file": changed,
        "registry_count": registry_count(toplevel, registry_dir),
    })

    # Nothing to run? Done.
    raw = read_commands(toplevel, cache_dir)
    commands = [
        line.rstrip()
        for line in raw.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not commands:
        return 0

    dpath = debug_path(cache_dir)
    dlog(dpath, "FIRE", f"changed={changed or '<none>'}", f"cmds={len(commands)}")

    def run_and_log(c):
        start = time.monotonic()
        cmd, status, snippet = run_one(c, changed_files, env)
        dlog(dpath, status, f"{time.monotonic() - start:.2f}s", cmd)
        return cmd, status, snippet

    # Run all commands in parallel; per-command 3s timeout enforces the budget.
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(commands)) as pool:
        results = list(pool.map(run_and_log, commands))

    # Log overall result so the $metrics skill can detect FAIL → PASS self-corrections.
    agg = "fail" if any(s in ("FAIL", "TIMEOUT") for _, s, _ in results) else "pass"
    log_metric(cache_dir, {"event": "feedback", "file": changed, "result": agg})

    # Format pass/fail/snippet per command for the agent-facing summary.
    summary_lines = []
    for cmd, status, snippet in results:
        if status == "FAIL" and snippet:
            summary_lines.append(f"{cmd}\tFAIL\t{snippet}")
        else:
            summary_lines.append(f"{cmd}\t{status}")
    summary = "\n".join(summary_lines)

    # Warn if this edit dropped the test-file count (Beck's "agent deletes tests" anti-pattern).
    warn = ""
    test_count_file = cache_dir / "test-count"
    now = test_count(toplevel)
    if now is not None and not test_count_file.is_file():
        # Seed the baseline on first run instead of relying on the agent to do it.
        try:
            test_count_file.parent.mkdir(parents=True, exist_ok=True)
            test_count_file.write_text(str(now), encoding="utf-8")
        except OSError:
            pass
    if now is not None and test_count_file.is_file():
        prev = None
        try:
            prev = int(test_count_file.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            pass
        if prev is not None and now != prev:
            if now < prev:
                warn = f"WARNING: this edit removed {prev - now} test file(s) (was {prev}, now {now})."
            try:
                test_count_file.write_text(str(now), encoding="utf-8")
            except OSError:
                pass

    if not summary and not warn:
        return 0

    parts = []
    if summary:
        parts.append(f"debt-ops feedback (3s budget per command):\n{summary}")
    if warn:
        parts.append(warn)
    emit("\n\n".join(parts))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # A bug here must never block the tool cycle.
        sys.exit(0)
