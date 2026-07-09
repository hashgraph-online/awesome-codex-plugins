#!/usr/bin/env python3
"""debt-ops register helper: silent entry writer + turn-batch letter assigner.

Codex adapter. Writing through this helper keeps the agent's mid-turn footprint
to one line — the helper's own stdout — and assigns a short letter (A, B, C, ...)
per entry so the user can later say `drop A` (handled by drop.py).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REQUIRED_FIELDS = (
    "slug", "principal", "interest", "hotspot",
    "business_capability", "payoff_trigger", "quadrant", "category", "ai_authored",
)

DEFAULT_REGISTRY_DIR = "docs/debt"


# Single deterministic cache base, shared verbatim with the hooks (ADR 0011).
# Both the hook subprocess (which gets PLUGIN_DATA) and this skill Bash env
# (which does not) land on the same dir, so the letter file this writes is the
# one drop.py reads. Override with DEBT_OPS_CACHE.
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


# A, B, ..., Z, AA, AB, ..., ZZ, AAA — base-26 column-style labels.
def letter_for(n):
    s = ""
    n += 1
    while n > 0:
        n -= 1
        s = chr(ord("A") + n % 26) + s
        n //= 26
    return s


# Append one JSON line to metrics.jsonl in the cache dir; silent no-op on failure.
def log_metric(cache_dir, payload):
    if not cache_dir.is_dir():
        return
    payload["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with (cache_dir / "metrics.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, separators=(",", ":")) + "\n")
    except OSError:
        pass


def parse_args():
    p = argparse.ArgumentParser(description="Register a debt entry silently.")
    p.add_argument("--slug", required=True, help="kebab-case label, 1-4 words")
    p.add_argument("--principal", required=True, help="effort to fix, or 'unknown'")
    p.add_argument("--interest", required=True, help="ongoing cost, or 'unknown'")
    p.add_argument("--hotspot", required=True, help="path or module, or 'unknown'")
    p.add_argument("--business-capability", required=True, dest="business_capability")
    p.add_argument("--payoff-trigger", required=True, dest="payoff_trigger")
    p.add_argument("--quadrant", required=True,
                   choices=["reckless-inadvertent", "reckless-deliberate",
                            "prudent-inadvertent", "prudent-deliberate"])
    p.add_argument("--category", required=True,
                   choices=["migration", "documentation", "testing", "code_quality",
                            "dead_code", "code_rot", "expertise", "release",
                            "infrastructure", "planning"])
    p.add_argument("--ai-authored", required=True, choices=["true", "false"],
                   dest="ai_authored")
    return p.parse_args()


def main():
    args = parse_args()

    toplevel = git_toplevel()
    if toplevel is None:
        sys.stderr.write("debt-ops: not in a git repo\n")
        return 2

    body = sys.stdin.read().strip()
    if not body:
        sys.stderr.write("debt-ops: empty body on stdin (pipe markdown via heredoc)\n")
        return 2

    now = time.localtime()
    entry_id = time.strftime("%Y%m%d%H%M%S", now)
    created = time.strftime("%Y-%m-%d", now)

    cache_dir = cache_base() / "cache" / repo_hash(toplevel)
    registry_rel = read_registry_dir(cache_dir)
    registry = toplevel / registry_rel
    registry.mkdir(parents=True, exist_ok=True)

    # Collision-safe path: parallel registrations within the same second get -2, -3, ...
    candidate = registry / f"{entry_id}-{args.slug}.md"
    i = 2
    while candidate.exists():
        candidate = registry / f"{entry_id}-{args.slug}-{i}.md"
        i += 1

    frontmatter = (
        "---\n"
        f"id: {entry_id}\n"
        f"title: {args.slug}\n"
        f"principal: {args.principal}\n"
        f"interest: {args.interest}\n"
        f"hotspot: {args.hotspot}\n"
        f"business_capability: {args.business_capability}\n"
        f"payoff_trigger: {args.payoff_trigger}\n"
        f"quadrant: {args.quadrant}\n"
        f"category: {args.category}\n"
        f"ai_authored: {args.ai_authored}\n"
        f"created: {created}\n"
        "---\n\n"
    )
    candidate.write_text(frontmatter + body + "\n", encoding="utf-8")

    # Assign a turn-batch letter by counting existing rows in current-turn.txt.
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Read-only cache: file is written, but letter shorthand won't work.
        sys.stdout.write(f"+1 entry: {args.slug}\n")
        return 0

    turn_file = cache_dir / "current-turn.txt"
    existing = 0
    if turn_file.is_file():
        try:
            existing = sum(1 for ln in turn_file.read_text(encoding="utf-8").splitlines() if ln.strip())
        except OSError:
            existing = 0
    letter = letter_for(existing)
    try:
        with turn_file.open("a", encoding="utf-8") as f:
            f.write(f"{letter}\t{args.slug}\t{candidate.name}\n")
    except OSError:
        pass

    log_metric(cache_dir, {
        "event": "register",
        "slug": args.slug,
        "ai_authored": args.ai_authored == "true",
        "letter": letter,
    })

    sys.stdout.write(f"+1 entry: {args.slug} ({letter})\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"debt-ops register: {e}\n")
        sys.exit(1)
