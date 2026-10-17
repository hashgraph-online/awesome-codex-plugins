#!/usr/bin/env python3
"""debt-ops SessionStart hook: emit disciplines + (charter | cache | discovery prompt).

Codex adapter. Mirrors the Claude hook but reads/writes AGENTS.md (Codex's
charter file) and resolves the cache from one deterministic base so the
skill Bash env agrees with the hook subprocess (ADR 0011).

Path adaptivity: cheap Python probe of common ADR/registry conventions on first
session, cached at <cache>/adr-dir and <cache>/registry-dir. If the probe finds
no existing ADR directory, the inject asks Codex to detect it semantically and
write the path itself — same pattern as the quality-commands detection below.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

CHARTER_MARKER = "<!-- debt-ops:feedback v1 -->"
MANIFEST_FILES = ("Cargo.toml", "package.json", "pyproject.toml", "Makefile", "go.mod", "Gemfile")

ADR_CANDIDATE_PATHS = (
    "doc/adr", "docs/adr", "doc/adrs", "docs/adrs",
    "adr", "adrs",
    "architecture/decisions", "docs/architecture/decisions", "doc/architecture/decisions",
)

REGISTRY_CANDIDATE_PATHS = (
    "docs/debt", "docs/registry", "doc/debt",
    "debt/registry", "tech-debt/registry", "debt-registry", "registry",
)

ADR_FILENAME_RE = re.compile(r"^\d+[-_].*\.md$", re.IGNORECASE)
# Co-located default home (ADR 0009): both artifacts under one `docs/` parent.
DEFAULT_ADR_DIR = "docs/adr"
DEFAULT_REGISTRY_DIR = "docs/debt"


# Single deterministic cache base so hook subprocesses and skill Bash (which
# never sees PLUGIN_DATA) resolve the same path. Override with DEBT_OPS_CACHE.
def cache_base():
    override = os.environ.get("DEBT_OPS_CACHE")
    return Path(override) if override else (Path.home() / ".cache" / "debt-ops")


def emit(context):
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    sys.stdout.write(json.dumps(payload) + "\n")


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


def repo_hash(toplevel):
    return hashlib.sha1(str(toplevel).encode()).hexdigest()[:12]


def manifest_hash(toplevel):
    paths = [toplevel / n for n in MANIFEST_FILES if (toplevel / n).is_file()]
    if not paths:
        return "no-manifest"
    try:
        joined = "\n".join(f"{int(p.stat().st_mtime)} {p}" for p in paths)
    except OSError:
        return "stat-failed"
    return hashlib.sha1(joined.encode()).hexdigest()[:12]


def md_count(dir_path):
    if not dir_path.is_dir():
        return 0
    try:
        return sum(1 for p in dir_path.iterdir() if p.is_file() and p.suffix == ".md")
    except OSError:
        return 0


def ai_authored_count(registry_dir):
    if not registry_dir.is_dir():
        return 0
    n = 0
    try:
        for p in registry_dir.iterdir():
            if p.is_file() and p.suffix == ".md":
                try:
                    if "ai_authored: true" in p.read_text(encoding="utf-8", errors="replace"):
                        n += 1
                except OSError:
                    pass
    except OSError:
        return 0
    return n


def log_metric(cache_dir, payload):
    if not cache_dir.is_dir():
        return
    payload["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with (cache_dir / "metrics.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, separators=(",", ":")) + "\n")
    except OSError:
        pass


def has_charter(toplevel):
    agents_md = toplevel / "AGENTS.md"
    if not agents_md.is_file():
        return False
    try:
        return CHARTER_MARKER in agents_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


# Read a cached relative path. Returns the string if the cache file exists,
# its content is non-empty, AND the path still resolves to a real directory
# under toplevel. Otherwise None — triggers re-detection.
def read_cached_dir(cache_file, toplevel):
    if not cache_file.is_file():
        return None
    try:
        rel = cache_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not rel:
        return None
    if not (toplevel / rel).is_dir():
        return None
    return rel


def write_cached_dir(cache_file, rel_path):
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(rel_path, encoding="utf-8")
    except OSError:
        pass


# Look for any ADR-shaped file (numbered-prefix .md) in known convention dirs.
# Returns the relative path or None if no convention matches with content.
def probe_adr_dir(toplevel):
    for rel in ADR_CANDIDATE_PATHS:
        p = toplevel / rel
        if not p.is_dir():
            continue
        try:
            for f in p.iterdir():
                if f.is_file() and ADR_FILENAME_RE.match(f.name):
                    return rel
        except OSError:
            pass
    return None


# Look for an existing registry dir with any .md content. Less variable than
# ADRs (plugin owns the convention), so we just check known shapes and fall
# back to the default.
def probe_registry_dir(toplevel):
    for rel in REGISTRY_CANDIDATE_PATHS:
        p = toplevel / rel
        if not p.is_dir():
            continue
        try:
            if any(f.is_file() and f.suffix == ".md" for f in p.iterdir()):
                return rel
        except OSError:
            pass
    return None


# When the ADR or registry dir doesn't exist yet, the inject states the
# co-location convention as fact and lets Codex pick the home — it reads the
# repo's doc conventions better than a fixed probe (ADR 0009). Codex writes
# the resolved repo-relative path(s) to the cache file(s) the other hooks read.
def placement_instruction(cache_dir, adr_dir, registry_dir):
    lines = ["Directory placement — resolve silently, no announcement:"]
    if adr_dir:
        lines.append(f"- ADRs already live at `{adr_dir}`.")
    if registry_dir:
        lines.append(f"- The debt registry already lives at `{registry_dir}`.")
    # ADRs vary more than the plugin-owned registry; check for a non-standard
    # existing dir before treating it as greenfield.
    if adr_dir is None:
        lines.append(
            "- No ADR directory was detected. First check whether one already exists "
            "in a non-standard spot — a dir of markdown with numbered filenames "
            "(`NNNN-title.md`) or Nygard sections (`## Context`, `## Decision`, "
            "`## Consequences`). Use it if it exists."
        )
    lines.append(
        "- debt-ops co-locates ADRs and the debt registry under one documentation "
        "home. When creating either from scratch, prefer an existing docs home "
        "(`docs/`, `documentation/`, or `doc/`); otherwise the home is `docs/`."
    )
    if adr_dir is None and registry_dir is None:
        lines.append(
            f"- With no home yet, use `<home>/adr` and `<home>/debt` "
            f"(defaults: `{DEFAULT_ADR_DIR}` + `{DEFAULT_REGISTRY_DIR}`)."
        )
    elif adr_dir is None:
        lines.append(
            f"- Place the ADR dir under the same home as the registry above so they "
            f"stay co-located, or default to `{DEFAULT_ADR_DIR}`."
        )
    else:
        lines.append(
            f"- Place the registry dir under the same home as the ADRs above so they "
            f"stay co-located, or default to `{DEFAULT_REGISTRY_DIR}`."
        )
    targets = []
    if adr_dir is None:
        targets.append(f"the ADR path to {cache_dir}/adr-dir")
    if registry_dir is None:
        targets.append(f"the registry path to {cache_dir}/registry-dir")
    lines.append(
        "- Write " + " and ".join(targets) + ", repo-relative, one path per file. "
        "Directories are created lazily on first write — no need to create them now."
    )
    return "\n".join(lines)


def commands_block(cache_dir, manifest, charter, stateless):
    if charter:
        return (
            f"Quality commands: read the AGENTS.md section marked `{CHARTER_MARKER}`. "
            "AGENTS.md is the source of truth when present."
        )
    if stateless:
        return (
            "debt-ops: cache disabled (read-only cache dir). "
            "For this session, detect quality commands once and run them yourself under timeout 3."
        )
    list_file = cache_dir / "feedback.list"
    hash_file = cache_dir / "manifest.hash"
    cached = ""
    if hash_file.is_file():
        try:
            cached = hash_file.read_text(encoding="utf-8").strip()
        except OSError:
            pass
    if list_file.is_file() and cached == manifest:
        try:
            return (
                "Cached quality commands (one per line; comment lines are estimates):\n"
                + list_file.read_text(encoding="utf-8")
            )
        except OSError:
            pass
    return (
        "First session for this repo (or manifest changed). Please do the following silently — no need to announce:\n\n"
        "1. Detect this project's quality commands by scanning manifest files (Cargo.toml, package.json, pyproject.toml, Makefile, go.mod, Gemfile) and tool-specific config (eslint, biome, ruff, mypy, tsconfig, etc.).\n"
        "2. Prefer commands that accept a changed-file or changed-package argument (e.g., `eslint $CHANGED_FILES`, `cargo clippy --no-deps -p $CHANGED_PACKAGE`, `pytest path/to/dir`) over project-wide ones.\n"
        "3. Reject any command whose typical wall-clock on this repo exceeds 3 seconds. Project-wide commands almost always exceed this on non-trivial repos.\n"
        f"4. Write to {cache_dir}/feedback.list. Format: one command per line, with the wall-clock estimate as a preceding comment, e.g.:\n"
        "   # est ~0.8s — fast type check\n"
        "   tsc --noEmit -p tsconfig.json\n"
        "   Comments (#) and empty lines are skipped when feedback.py reads the file.\n"
        f"5. Write the manifest hash to {cache_dir}/manifest.hash with this exact value: {manifest}\n"
        f"6. Count test-shaped filenames in the repo (filenames matching test_*, *_test.*, *.test.*, or *.spec.*) and write the integer count to {cache_dir}/test-count. feedback.py recomputes this on every edit and warns when it drops."
    )


# Substitutes the detected paths into the disciplines text. Discipline 2 names
# the ADR dir Codex should write new ADRs into; Discipline 3 names the
# registry to read before editing referenced files.
def disciplines_text(adr_dir, registry_dir):
    return (
        '1. The test for debt: would a future reader ask "why this way?" If yes, register via the '
        '`$add` skill immediately — no prompt. This is judgment, not a marker scan: a '
        '`TODO`/`FIXME`/`HACK`/`XXX` is the obvious case, but an unmade decision, a stub, a loosened '
        'type, or a default picked "for now" all count even with no marker in the diff. Use '
        '`payoff_trigger: unknown` if unsure. The helper prints one line: `+1 entry: <slug> '
        '(<letter>)` — don\'t paraphrase or add commentary. Over-register freely; the developer drops '
        'with `drop A`, `drop A,C`, `drop all`, or `drop <slug>`.\n\n'
        '2. When making an architecturally significant change — a data model, public interface, '
        'security boundary, release pipeline, or a dep-manifest change that is a major-version bump '
        f'or a *new* top-level dependency — draft an ADR under {adr_dir}/ in Nygard format: a '
        '`# NNNN — Title` heading, `**Date:**` and `**Status:**` lines, then Context, Decision, Consequences, '
        'Alternatives, Payoff trigger. Create the directory if needed. Only draft an ADR when there '
        'are two credible alternatives; if you cannot list two, it is a comment, not an ADR. An ADR '
        'with a payoff trigger *is* deliberate debt — when you write one, also invoke `$add` so the '
        'registry entry mirrors the ADR (don\'t conclude "no markers, no debt").\n\n'
        f'3. Read entries under {registry_dir}/ before changing files they reference.'
    )


def main():
    toplevel = git_toplevel()
    if toplevel is None:
        emit("debt-ops: not a git repo, plugin idle this session")
        return 0

    cache_dir = cache_base() / "cache" / repo_hash(toplevel)
    stateless = False
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        stateless = True

    # Resolve ADR and registry paths: cached → existing-content probe. Either
    # may stay None (greenfield) — the placement inject below then has Codex
    # choose a co-located home and write the cache file(s). See ADR 0009.
    adr_cache = cache_dir / "adr-dir"
    registry_cache = cache_dir / "registry-dir"

    adr_dir = read_cached_dir(adr_cache, toplevel)
    if adr_dir is None:
        probed = probe_adr_dir(toplevel)
        if probed:
            adr_dir = probed
            if not stateless:
                write_cached_dir(adr_cache, probed)

    registry_dir = read_cached_dir(registry_cache, toplevel)
    if registry_dir is None:
        probed = probe_registry_dir(toplevel)
        if probed:
            registry_dir = probed
            if not stateless:
                write_cached_dir(registry_cache, probed)

    effective_adr_dir = adr_dir or DEFAULT_ADR_DIR
    effective_registry_dir = registry_dir or DEFAULT_REGISTRY_DIR

    log_metric(cache_dir, {
        "event": "session",
        "registry_count": md_count(toplevel / effective_registry_dir),
        "adr_count": md_count(toplevel / effective_adr_dir),
        "ai_authored_count": ai_authored_count(toplevel / effective_registry_dir),
        "adr_dir": effective_adr_dir,
        "registry_dir": effective_registry_dir,
    })

    context = (
        "Tech-debt-operations disciplines (debt-ops plugin):\n\n"
        f"{disciplines_text(effective_adr_dir, effective_registry_dir)}\n\n"
        f"{commands_block(cache_dir, manifest_hash(toplevel), has_charter(toplevel), stateless)}"
    )
    if (adr_dir is None or registry_dir is None) and not stateless:
        context += "\n\n" + placement_instruction(cache_dir, adr_dir, registry_dir)
    if not stateless:
        context += (
            f"\n\nDebug: set DEBT_OPS_DEBUG=1 in the environment to log every hook fire "
            f"and command result to {cache_dir}/debug.log (tab-separated; tail -f to watch)."
        )
    emit(context)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
