#!/usr/bin/env python3
"""debt-ops review: audit registry for stale entries + rank survivors by churn × quadrant.

Codex adapter. Audit signals (deterministic, Git-as-oracle):
- (a) hotspot path exists in the repo — strong "stale" signal when missing
- (b) commits touching the hotspot since the entry's created date — used for
  ranking and for cold-area detection, not for staleness alone

The marker-presence heuristic was considered and cut: most registry entries
describe architectural deferrals (unfinished features, undecided shapes,
validation gaps) that never had an in-code TODO. A "no markers in file"
check fired on 100% of slack-agent's 83 entries in dogfood — a clear sign
the signal is wrong for this registry shape. Without ground-truth on the
marker at register time, we err on the side of not auto-flagging stale.

Ranking (survivors only):
- score = churn × quadrant_weight + ai_authored_bonus + age_bonus
- quadrant weights track Fowler triage: reckless-inadvertent first (3),
  reckless-deliberate (2), prudent-inadvertent (2), prudent-deliberate (1).

Side effects:
- Writes letter mappings for stale entries to current-turn.txt so the user
  can drop them with the existing `drop A,B,C` UX.

The output is a one-screen, three-bucket report intended to be the entire
user-facing reply when the review skill fires.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_REGISTRY_DIR = "docs/debt"
QUADRANT_WEIGHT = {
    "reckless-inadvertent": 3,
    "reckless-deliberate": 2,
    "prudent-inadvertent": 2,
    "prudent-deliberate": 1,
}

# Plain-language labels for display. The canonical Fowler quadrant stays in the
# frontmatter + scoring; developers read these instead of the academic terms.
QUADRANT_PLAIN = {
    "reckless-inadvertent": "accidental",
    "reckless-deliberate": "knowing shortcut",
    "prudent-inadvertent": "came up later",
    "prudent-deliberate": "planned tradeoff",
}


# Single deterministic cache base, shared verbatim with the hooks (ADR 0011).
# Override with DEBT_OPS_CACHE.
def cache_base():
    override = os.environ.get("DEBT_OPS_CACHE")
    return Path(override) if override else (Path.home() / ".cache" / "debt-ops")


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


# Read session-start.py's cached registry-dir path; default if missing.
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


# Parse YAML-ish frontmatter into a dict; tolerant of missing fields.
def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm = {}
    for ln in text[3:end].strip().splitlines():
        if ":" not in ln:
            continue
        k, _, v = ln.partition(":")
        fm[k.strip()] = v.strip()
    return fm


# git log commit count touching <path> since <since> (YYYY-MM-DD); 0 on failure.
def churn_since(toplevel, path, since):
    if not path or path == "unknown":
        return 0
    args = ["git", "-C", str(toplevel), "log", "--oneline"]
    if since:
        args += [f"--since={since}"]
    args += ["--", path]
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=3)
        return sum(1 for ln in out.stdout.splitlines() if ln.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        return 0


def days_since(date_str):
    if not date_str:
        return 0
    try:
        t = time.strptime(date_str, "%Y-%m-%d")
        return max(0, int((time.time() - time.mktime(t)) / 86400))
    except ValueError:
        return 0


# Body preview: first non-empty line of prose after the frontmatter, ~85 chars.
def body_preview(text, max_chars=85):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            text = text[end + 4:]
    for ln in text.splitlines():
        s = ln.strip()
        if s and not s.startswith("#"):
            if len(s) <= max_chars:
                return s
            return s[: max_chars - 1].rstrip() + "…"
    return ""


# A, B, ..., Z, AA, AB — base-26 column-style (matches register.py).
def letter_for(n):
    s = ""
    n += 1
    while n > 0:
        n -= 1
        s = chr(ord("A") + n % 26) + s
        n //= 26
    return s


def audit_entry(toplevel, entry_path):
    """Return a dict of frontmatter + audit signals for one registry entry."""
    try:
        text = entry_path.read_text(encoding="utf-8")
    except OSError:
        return None
    fm = parse_frontmatter(text)
    slug = fm.get("title") or entry_path.stem
    hotspot = fm.get("hotspot", "unknown")
    created = fm.get("created", "")
    quadrant = fm.get("quadrant", "reckless-inadvertent")
    ai_authored = fm.get("ai_authored", "false").lower() == "true"

    target = (toplevel / hotspot) if hotspot and hotspot != "unknown" else None
    file_exists = target.exists() if target else None
    churn = churn_since(toplevel, hotspot, created) if (target and file_exists) else 0
    age = days_since(created)

    return {
        "fname": entry_path.name,
        "slug": slug,
        "hotspot": hotspot,
        "created": created,
        "age_days": age,
        "quadrant": quadrant,
        "ai_authored": ai_authored,
        "file_exists": file_exists,
        "churn_since_created": churn,
        "preview": body_preview(text),
    }


def classify(entry):
    """Return ('stale', reason) | ('cold', reason) | ('active', None).

    Only file-missing flags as stale outright (the one signal we trust at 100%).
    Long-dormant files become cold (deprioritize). Everything else stays active
    so the user — not the script — decides what's still real.
    """
    if entry["file_exists"] is False:
        return ("stale", "hotspot file missing")
    if entry["file_exists"] is True and entry["churn_since_created"] == 0 and entry["age_days"] > 90:
        return ("cold", f"unchanged in {entry['age_days']}d")
    return ("active", None)


def score(entry):
    """Higher = more important to pay down. Behavioral signal × Fowler triage."""
    weight = QUADRANT_WEIGHT.get(entry["quadrant"], 1)
    base = entry["churn_since_created"] * weight
    if entry["ai_authored"]:
        base += 2  # leading-indicator bonus, per docs/tech-debt-plugin-plan.md:815
    if entry["age_days"] > 30:
        base += 1  # mild age penalty for aged-out entries
    return base


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


def write_stale_letters(cache_dir, stale_entries):
    """Append letter mappings for stale entries to current-turn.txt so `drop A,B,C` works."""
    if not stale_entries:
        return {}
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return {}
    turn_file = cache_dir / "current-turn.txt"
    existing = 0
    if turn_file.is_file():
        try:
            existing = sum(1 for ln in turn_file.read_text(encoding="utf-8").splitlines() if ln.strip())
        except OSError:
            existing = 0
    mapping = {}
    try:
        with turn_file.open("a", encoding="utf-8") as f:
            for i, e in enumerate(stale_entries):
                L = letter_for(existing + i)
                f.write(f"{L}\t{e['slug']}\t{e['fname']}\n")
                mapping[L] = e
    except OSError:
        pass
    return mapping


def print_report(stale_map, top, cold, active_kept_count):
    lines = []
    n_stale = len(stale_map)
    lines.append(f"debt-ops review — {n_stale + len(top) + len(cold) + active_kept_count} entries")
    lines.append("─────────────────────────────────")

    if stale_map:
        lines.append(f"likely stale ({n_stale}) — drop with `drop A,B,…` or `drop all`")
        for L, e in stale_map.items():
            lines.append(f"  {L}  {e['slug']:<40} ({e['_reason']})")
        lines.append("")

    if top:
        lines.append(f"top {len(top)} to pay down")
        for e in top:
            tag = " [ai]" if e["ai_authored"] else ""
            plain = QUADRANT_PLAIN.get(e["quadrant"], e["quadrant"])
            n = e["churn_since_created"]
            edits = f"{n} edit{'' if n == 1 else 's'} since logged"
            lines.append(
                f"  • {e['slug']:<40} {e['hotspot']} · {plain} · {edits}{tag}"
            )
            if e["preview"]:
                lines.append(f"    {e['preview']}")
        lines.append("")

    if cold:
        lines.append(f"cold ({len(cold)}) — deprioritize; revisit on next hot edit")
        for e in cold[:5]:
            lines.append(f"  · {e['slug']:<40} ({e['_reason']})")
        if len(cold) > 5:
            lines.append(f"  · …and {len(cold) - 5} more")
        lines.append("")

    if active_kept_count:
        lines.append(f"kept ({active_kept_count}) — active, lower-ranked; rerun the review skill after paydown")

    sys.stdout.write("\n".join(lines).rstrip() + "\n")


def parse_args():
    p = argparse.ArgumentParser(description="Audit + rank the debt registry.")
    p.add_argument("--top", type=int, default=3, help="how many top-paydown entries to surface (default 3)")
    return p.parse_args()


def main():
    args = parse_args()

    toplevel = git_toplevel()
    if toplevel is None:
        sys.stderr.write("debt-ops: not in a git repo\n")
        return 2

    cache_dir = cache_base() / "cache" / repo_hash(toplevel)
    registry = toplevel / read_registry_dir(cache_dir)

    if not registry.is_dir():
        sys.stdout.write(f"debt-ops review: no registry at {registry.relative_to(toplevel)} — nothing to review.\n")
        return 0

    entries = []
    for f in sorted(registry.glob("*.md")):
        e = audit_entry(toplevel, f)
        if e is not None:
            entries.append(e)

    if not entries:
        sys.stdout.write("debt-ops review: registry empty — nothing to review.\n")
        return 0

    stale, cold, active = [], [], []
    for e in entries:
        bucket, reason = classify(e)
        e["_reason"] = reason
        if bucket == "stale":
            stale.append(e)
        elif bucket == "cold":
            cold.append(e)
        else:
            active.append(e)

    active.sort(key=score, reverse=True)
    top = active[:args.top]
    kept = active[args.top:]

    stale_map = write_stale_letters(cache_dir, stale)
    log_metric(cache_dir, {
        "event": "review",
        "total": len(entries),
        "stale": len(stale),
        "cold": len(cold),
        "active": len(active),
    })
    print_report(stale_map, top, cold, len(kept))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"debt-ops review: {e}\n")
        sys.exit(1)
