#!/usr/bin/env python3
"""debt-ops Stop hook: TODO-sniff safety net for Discipline 1.

Codex adapter. Fires at the end of every turn. Counts newly-added marker lines
(TODO/FIXME/HACK/XXX) in the working tree vs newly-added entries under the
registry dir. If markers > registrations, nudges Codex on the next turn via a
`decision: block` continuation.

Tripwire, not precision: false positives are cheap (the dev drops
spurious entries with "drop it"); false negatives defeat the point.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

DEBUG_ENV = "DEBT_OPS_DEBUG"
MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
# Plugin-source prefixes are always excluded (this monorepo hosts every
# adapter); debt-registry and ADR prefixes are looked up per-repo from the
# cache files written by session-start.py. See build_excluded_prefixes below.
STATIC_EXCLUDED_PREFIXES = ("claude-code/", "codex/", "copilot/", "cursor/", "skills/")
DEFAULT_REGISTRY_DIR = "docs/debt"
DEFAULT_ADR_DIR = "docs/adr"
MAX_UNTRACKED_BYTES = 1_000_000
# Hard cap on Stop-hook blocks per session. After this many blocks fire
# for a given session_id, all subsequent Stop calls in that session stay
# silent — bounds any pathological loop and respects the "more behind
# the scenes" posture. SessionStart resets the counter implicitly via a
# new session_id from the hook payload.
SESSION_BLOCK_CAP = 1


# Single deterministic cache base so hook subprocesses and skill Bash (which
# never sees PLUGIN_DATA) resolve the same path. Override with DEBT_OPS_CACHE.
def cache_base():
    override = os.environ.get("DEBT_OPS_CACHE")
    return Path(override) if override else (Path.home() / ".cache" / "debt-ops")


# Emit a block decision. `decision: "block"` + `reason` is the documented way
# to make Codex continue working on the supplied message before stopping.
def emit(reason):
    payload = {
        "decision": "block",
        "reason": reason,
    }
    sys.stdout.write(json.dumps(payload) + "\n")


# Resolve repo root; returns None outside a git repo so we idle cleanly.
def git_toplevel():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, timeout=2,
        )
        s = out.stdout.strip()
        return Path(s) if s else None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def repo_hash(toplevel):
    return hashlib.sha1(str(toplevel).encode()).hexdigest()[:12]


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
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write("\t".join((ts,) + fields) + "\n")
    except OSError:
        pass


# Resolve registry/ADR paths from cache (written by session-start.py); fall
# back to defaults if cache missing. Returns ("docs/debt", "docs/adr") shape.
def resolve_dirs(cache_dir):
    def read(name, default):
        p = cache_dir / name
        if p.is_file():
            try:
                val = p.read_text(encoding="utf-8").strip()
                if val:
                    return val
            except OSError:
                pass
        return default
    return read("registry-dir", DEFAULT_REGISTRY_DIR), read("adr-dir", DEFAULT_ADR_DIR)


def build_excluded_prefixes(registry_dir, adr_dir):
    return tuple(f"{d.rstrip('/')}/" for d in (registry_dir, adr_dir)) + STATIC_EXCLUDED_PREFIXES


# True if the file path is excluded from marker counting.
def is_excluded(path, excluded_prefixes):
    return any(path.startswith(p) for p in excluded_prefixes)


# Counts marker hits in `+` lines from `git diff HEAD` (modified-tracked files).
def markers_in_diff(toplevel, excluded_prefixes):
    try:
        out = subprocess.run(
            ["git", "diff", "HEAD", "--", "."],
            cwd=toplevel,
            capture_output=True, text=True, timeout=2,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return 0
    # rc 0 = no diff or success; rc 1 from git diff also signals "differences found" in some contexts.
    if out.returncode not in (0, 1):
        return 0
    n = 0
    current_path = None
    for line in out.stdout.splitlines():
        if line.startswith("+++ b/"):
            p = line[6:]
            current_path = None if p == "/dev/null" else p
            continue
        if line.startswith("+++"):
            current_path = None
            continue
        if not line.startswith("+"):
            continue
        if current_path is None or is_excluded(current_path, excluded_prefixes):
            continue
        if MARKER_RE.search(line):
            n += 1
    return n


# Counts marker hits in untracked files (whole file = new lines).
def markers_in_untracked(toplevel, excluded_prefixes):
    try:
        out = subprocess.run(
            ["git", "ls-files", "-o", "--exclude-standard"],
            cwd=toplevel,
            capture_output=True, text=True, timeout=2,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return 0
    if out.returncode != 0:
        return 0
    n = 0
    for path in out.stdout.splitlines():
        if is_excluded(path, excluded_prefixes):
            continue
        full = toplevel / path
        try:
            if not full.is_file() or full.stat().st_size > MAX_UNTRACKED_BYTES:
                continue
            text = full.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if MARKER_RE.search(line):
                n += 1
    return n


# True if this turn produced any tracked-or-untracked file change outside
# the excluded paths (registry/ADR). Used to gate stage-2 broad-judgment
# blocks so we don't fire on no-op turns or doc-only edits.
def has_code_changes(toplevel, excluded_prefixes):
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=toplevel,
            capture_output=True, text=True, timeout=2,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        out = None
    if out and out.returncode in (0, 1):
        for path in out.stdout.splitlines():
            if path.strip() and not is_excluded(path, excluded_prefixes):
                return True
    try:
        out2 = subprocess.run(
            ["git", "ls-files", "-o", "--exclude-standard"],
            cwd=toplevel,
            capture_output=True, text=True, timeout=2,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
    if out2.returncode == 0:
        for path in out2.stdout.splitlines():
            if path.strip() and not is_excluded(path, excluded_prefixes):
                return True
    return False


# Fingerprint of the current decidable state. The Stop hook re-runs at the
# end of every assistant turn; without this, stages 1 and 2 would re-fire
# every turn on an unchanged pending diff and trap the agent in an
# "Acknowledged, no changes" loop until the user commits.
def state_fingerprint(toplevel, stage, markers, entries):
    h = hashlib.sha1()
    h.update(f"{stage}|{markers}|{entries}|".encode())
    try:
        out = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=toplevel, capture_output=True, text=True, timeout=2,
        )
        h.update(out.stdout.encode("utf-8", errors="replace"))
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    h.update(b"\x00")
    try:
        out = subprocess.run(
            ["git", "ls-files", "-o", "--exclude-standard"],
            cwd=toplevel, capture_output=True, text=True, timeout=2,
        )
        h.update(out.stdout.encode("utf-8", errors="replace"))
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return h.hexdigest()


def already_nudged(state_path, fingerprint):
    try:
        return state_path.read_text(encoding="utf-8").strip() == fingerprint
    except OSError:
        return False


def record_nudge(state_path, fingerprint):
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(fingerprint, encoding="utf-8")
    except OSError:
        pass


# Counts new (untracked or staged-add) .md files under the registry dir.
# Pathspec scopes the call so `--untracked-files=all` (needed to walk into
# fully-untracked registry dirs) doesn't expand work over the whole repo.
def new_registry_entries(toplevel, registry_dir):
    pathspec = f"{registry_dir.rstrip('/')}/"
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", pathspec],
            cwd=toplevel,
            capture_output=True, text=True, timeout=2,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return 0
    if out.returncode != 0:
        return 0
    n = 0
    for line in out.stdout.splitlines():
        if len(line) < 4:
            continue
        status = line[:2]
        path = line[3:].strip()
        # Renames look like "R  oldname -> newname"; we want the new name.
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        # Strip git's quoting around paths with special chars.
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        if not path.startswith(pathspec) or not path.endswith(".md"):
            continue
        # New = untracked (??) or any add in either status column.
        if status == "??" or "A" in status:
            n += 1
    return n


def parse_stdin():
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {}


# Read the per-session block counter. Returns 0 if file missing OR stored
# session_id doesn't match — the latter implicitly resets the count on a
# new session without needing SessionStart to do anything.
def session_block_count(path, session_id):
    if not path.is_file():
        return 0
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return 0
    parts = text.split("\t", 1)
    if len(parts) != 2:
        return 0
    if parts[0] != session_id:
        return 0
    try:
        return int(parts[1])
    except ValueError:
        return 0


def record_session_block(path, session_id, count):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{session_id}\t{count}", encoding="utf-8")
    except OSError:
        pass


def main():
    data = parse_stdin()
    session_id = str(data.get("session_id") or "")

    toplevel = git_toplevel()
    if toplevel is None:
        return 0

    cache_dir = cache_base() / "cache" / repo_hash(toplevel)
    dpath = debug_path(cache_dir)
    state_path = cache_dir / "stop-state"
    session_blocks_path = cache_dir / "session-blocks"

    registry_dir, adr_dir = resolve_dirs(cache_dir)
    excluded_prefixes = build_excluded_prefixes(registry_dir, adr_dir)

    markers = markers_in_diff(toplevel, excluded_prefixes) + markers_in_untracked(toplevel, excluded_prefixes)
    entries = new_registry_entries(toplevel, registry_dir)

    # Per-session block cap (outer gate). If we've already blocked once
    # this session, stay silent regardless of state — bounds loops and
    # respects the "more behind the scenes" posture.
    blocks_this_session = session_block_count(session_blocks_path, session_id)
    capped = blocks_this_session >= SESSION_BLOCK_CAP

    if markers > entries:
        # Stage 1: specific marker-count block.
        fp = state_fingerprint(toplevel, "stage1", markers, entries)
        if already_nudged(state_path, fp):
            dlog(dpath, "STOP", f"markers={markers}", f"new_registry={entries}", "stage=1", "skipped=dup")
            return 0
        if capped:
            dlog(dpath, "STOP", f"markers={markers}", f"new_registry={entries}", "stage=1", f"skipped=cap({blocks_this_session})")
            return 0
        record_nudge(state_path, fp)
        record_session_block(session_blocks_path, session_id, blocks_this_session + 1)
        dlog(dpath, "STOP", f"markers={markers}", f"new_registry={entries}", "stage=1")
        delta = markers - entries
        reason = (
            f"debt-ops: {markers} marker(s), {entries} entry/entries — "
            f"register {delta} more via the $add skill."
        )
        emit(reason)
        return 0

    # Stage 2: no markers and no registrations, but code changed — let Codex
    # judge whether the diff contains broader Discipline 1 deferrals (stubs,
    # loosened types, swallowed errors, deferred-via-prose, mocked calls).
    if markers == 0 and entries == 0 and has_code_changes(toplevel, excluded_prefixes):
        fp = state_fingerprint(toplevel, "stage2", markers, entries)
        if already_nudged(state_path, fp):
            dlog(dpath, "STOP", f"markers={markers}", f"new_registry={entries}", "stage=2", "skipped=dup")
            return 0
        if capped:
            dlog(dpath, "STOP", f"markers={markers}", f"new_registry={entries}", "stage=2", f"skipped=cap({blocks_this_session})")
            return 0
        record_nudge(state_path, fp)
        record_session_block(session_blocks_path, session_id, blocks_this_session + 1)
        dlog(dpath, "STOP", f"markers={markers}", f"new_registry={entries}", "stage=2")
        # One-line nudge — the loaded add skill carries the full definition.
        reason = (
            "debt-ops: turn changed code, no entries registered — "
            "review your diff for deferrals."
        )
        emit(reason)
        return 0

    # Rotate this turn's batch into last-batch.txt so `drop A` resolves
    # against the just-completed turn on the next UserPromptSubmit. Only
    # runs on clean stops (stage 1/2 didn't fire) so re-fires under a
    # blocked stop don't clobber an earlier batch before Codex resolves.
    rotate_batch(cache_dir)
    dlog(dpath, "STOP", f"markers={markers}", f"new_registry={entries}", "silent")
    return 0


# Move current-turn.txt -> last-batch.txt atomically. Silent no-op if there's
# nothing to rotate.
def rotate_batch(cache_dir):
    src = cache_dir / "current-turn.txt"
    dst = cache_dir / "last-batch.txt"
    if not src.is_file():
        return
    try:
        os.replace(src, dst)
    except OSError:
        pass


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # A hook bug must never block the tool cycle — exit clean.
        sys.exit(0)
