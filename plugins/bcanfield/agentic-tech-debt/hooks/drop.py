#!/usr/bin/env python3
"""debt-ops UserPromptSubmit hook: handle 'drop A,B' / 'drop all' shorthand.

Codex adapter. When the user types `drop A`, `drop A,C`, or `drop all` as the
entire prompt, this hook deletes the matching entries from the most recent
batch and blocks the prompt with a one-line confirmation — no model turn
consumed.

Other "drop" forms ("drop it", "drop foo-slug") aren't matched and fall through
to the model's normal handling per the add skill.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Strict: full input must be 'drop' + 'all' OR 1-3 letters separated by commas/spaces.
# Trailing period optional. Case-insensitive.
# "drop it" doesn't match (i,t can't be one 1-3-char token without a separator
# — actually `it` IS two letters so [a-z]{1,3} matches it. Guard below).
DROP_RE = re.compile(
    r"^\s*drop\s+(all|[a-z]{1,3}(?:[\s,]+[a-z]{1,3})*)\s*\.?\s*$",
    re.IGNORECASE,
)

DEFAULT_REGISTRY_DIR = "docs/debt"


# Single deterministic cache base so hook subprocesses and skill Bash (which
# never sees PLUGIN_DATA) resolve the same path. Override with DEBT_OPS_CACHE.
def cache_base():
    override = os.environ.get("DEBT_OPS_CACHE")
    return Path(override) if override else (Path.home() / ".cache" / "debt-ops")


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


def emit_block(reason):
    payload = {
        "decision": "block",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": reason,
        },
        "reason": reason,
    }
    sys.stdout.write(json.dumps(payload) + "\n")


def log_metric(cache_dir, payload):
    if not cache_dir.is_dir():
        return
    payload["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with (cache_dir / "metrics.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, separators=(",", ":")) + "\n")
    except OSError:
        pass


def read_batch(path):
    """Parse `LETTER\tslug\tfname` rows into a dict keyed by uppercase letter."""
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    mapping = {}
    for ln in text.splitlines():
        parts = ln.split("\t")
        if len(parts) >= 3 and parts[0].strip():
            mapping[parts[0].strip().upper()] = (parts[1].strip(), parts[2].strip())
    return mapping


def write_batch(path, mapping):
    try:
        if not mapping:
            path.unlink(missing_ok=True)
            return
        lines = [f"{L}\t{slug}\t{fname}" for L, (slug, fname) in mapping.items()]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        pass


def main():
    try:
        raw = sys.stdin.read()
    except OSError:
        return 0
    if not raw:
        return 0
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return 0
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return 0

    m = DROP_RE.match(prompt)
    if not m:
        return 0

    # Guard: don't intercept "drop it" — let the model handle it conversationally.
    tokens = re.split(r"[\s,]+", m.group(1).strip().lower())
    if tokens == ["it"]:
        return 0

    toplevel = git_toplevel()
    if toplevel is None:
        return 0

    cache_dir = cache_base() / "cache" / repo_hash(toplevel)

    # Look in both files: current-turn.txt (just-finished turn, not yet rotated)
    # and last-batch.txt (turn before that). Merge with current-turn winning.
    current = read_batch(cache_dir / "current-turn.txt")
    last = read_batch(cache_dir / "last-batch.txt")
    mapping = {**last, **current}
    if not mapping:
        return 0

    if tokens == ["all"]:
        letters = list(mapping.keys())
    else:
        letters = [t.upper() for t in tokens]

    registry_dir = toplevel / read_registry_dir(cache_dir)
    deleted = []
    not_found = []
    for L in letters:
        if L not in mapping:
            not_found.append(L)
            continue
        slug, fname = mapping[L]
        target = registry_dir / fname
        try:
            target.unlink(missing_ok=True)
            deleted.append(slug)
            # Remove from whichever source file held it.
            current.pop(L, None)
            last.pop(L, None)
        except OSError:
            not_found.append(L)

    if not deleted:
        # Nothing actually deleted — pass through to the model so they can ask why.
        return 0

    write_batch(cache_dir / "current-turn.txt", current)
    write_batch(cache_dir / "last-batch.txt", last)

    log_metric(cache_dir, {"event": "drop", "slugs": deleted, "missed": not_found})

    parts = [f"Dropped: {', '.join(deleted)}."]
    if not_found:
        parts.append(f"Not in batch: {', '.join(not_found)}.")
    emit_block(" ".join(parts))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # A hook bug must never block the user's prompt — exit clean.
        sys.exit(0)
