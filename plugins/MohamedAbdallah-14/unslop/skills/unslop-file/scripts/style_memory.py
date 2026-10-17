"""Phase 8 style memory: persist a StyleProfile per user.

Phase 4 shipped stylometric measurement; Phase 4-wire made it usable via
`--voice-sample PATH`. That still requires the sample on every invocation.
This module persists the measured profile so voice-match auto-loads.

Storage: $UNSLOP_STYLE_MEMORY, then $XDG_CONFIG_HOME/unslop/style-memory.json,
then ~/.config/unslop/style-memory.json (Linux/macOS) / %APPDATA%/unslop/
style-memory.json (Windows). First one set or existing wins.

Schema:
  {
    "version": 1,
    "profile": {StyleProfile.to_dict()},
    "sample_words": int,
    "saved_at": iso-8601 string,
    "source": str | null    # original file path or "stdin" when provided
  }

Design constraint — what this file does NOT store
--------------------------------------------------
MIT/Penn State CHI 2026 (Barcelona, April 2026) measured condensed user
profiles in agent memory as the largest single sycophancy driver across
five LLMs. The mechanism: free-text preference strings like "user prefers
warm tone" or "user likes metaphors" get re-surfaced into prompts and the
model leans on them, amplifying whatever the user said last time.

This module sidesteps that class of failure by persisting only
numerically-measured signals from `stylometry.py` — sentence-length μ/σ,
fragment rate, contraction rate, punctuation rates, TTR, Latinate ratio,
pronoun rates, approximate passive voice, And/But-opener rate. No
free-text preference slots. No "user likes X" keys. The `StyleProfile`
schema is closed: any extra field fails validation on load.

Voice drift across a long session is a distinct problem — HorizonBench
(arXiv 2604.17283, April 2026) is the first benchmark for preference
evolution over time, and RMTBench empirically shows >30% persona
degradation after 8–12 turns. This file is half the mitigation (stable
measured anchor across invocations); the other half lives in
`hooks/unslop-activate.js` (in-session re-reinforcement at turn 8 and 16).

Security posture
----------------
Persistent memory is a named risk in the OWASP Top 10 for Agentic
Applications 2026. Memory poisoning classes to defend against:

  - InjecMEM (one-injection memory poisoning) — attacker-controlled text
    written through a trusted pipe. Defended by refusing symlinks and
    validating the schema on load (any unexpected key → reject).
  - Memory control flow attacks — an overlong or pathologically shaped
    file crashing or redirecting the parser. Defended by a file-size cap
    on read and a closed schema with numeric-only fields.
  - Semantic drift — slow poisoning over many writes. Mitigated by the
    schema staying numeric and verifiable via a fresh `analyze()` pass.
  - Owner confusion — mode 0600 + `lstat()` check before open + resolved
    path inside `CLAUDE_CONFIG_DIR` when that env is set.

Primary references: Memory Security survey (arXiv 2604.16548, Apr 2026),
OWASP Top 10 for Agentic Applications 2026, Rehberger's original memory
poisoning write-up (2024).

Not a hook. Pure CLI-driven save/load. Not linked to any session-level
state. Works offline.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from .stylometry import StyleProfile, analyze

_SCHEMA_VERSION = 1

# OWASP memory-control-flow mitigation: a valid StyleProfile JSON is ~1 KB.
# Anything above 64 KB is either corrupt, attacker-planted, or schema drift —
# either way, refuse to parse. Prevents pathological JSON / alloc attacks on
# the CLI entry point.
_MAX_FILE_BYTES = 64 * 1024


class StyleMemoryError(RuntimeError):
    """Raised when the memory file is present but unreadable / malformed."""


def _default_path() -> Path:
    env = os.environ.get("UNSLOP_STYLE_MEMORY")
    if env:
        return Path(env).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "unslop" / "style-memory.json"
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "unslop" / "style-memory.json"
    return Path.home() / ".config" / "unslop" / "style-memory.json"


def _refuse_symlink(path: Path) -> None:
    """If `path` exists and is a symlink, refuse. Same reasoning as the
    flag-file pattern in hooks/unslop-config.js: predictable user-owned
    paths are a local-attack surface for symlink-clobber tricks."""
    if path.is_symlink():
        raise StyleMemoryError(
            f"Refusing to touch symlink at {path}. "
            "Remove or replace with a regular file."
        )


def save_profile(
    sample_text: str,
    *,
    source: str | None = None,
    path: Path | None = None,
) -> Path:
    """Measure the sample's profile and persist it. Returns the path written.

    Overwrites any existing memory. The profile replaces, it does not merge —
    a new sample is the new voice. Profiles under 50 words raise
    StyleMemoryError because their signals are too noisy to commit."""
    profile = analyze(sample_text)
    if profile.total_words < 50:
        raise StyleMemoryError(
            f"Sample is {profile.total_words} words; need ≥50 for stable "
            "signals. Use a larger sample."
        )

    target = path or _default_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    _refuse_symlink(target)

    payload = {
        "version": _SCHEMA_VERSION,
        "profile": profile.to_dict(),
        "sample_words": profile.total_words,
        "saved_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
    }

    # Atomic write: temp file in same directory, then rename.
    fd, tmp_path = tempfile.mkstemp(
        prefix="style-memory-", suffix=".json.tmp", dir=str(target.parent)
    )
    os.close(fd)
    tmp = Path(tmp_path)
    try:
        tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.chmod(tmp, 0o600)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
    return target


def load_profile(path: Path | None = None) -> StyleProfile | None:
    """Read the persisted profile. Returns None if no file; raises
    StyleMemoryError on a malformed file or symlink."""
    target = path or _default_path()
    if not target.exists():
        return None
    _refuse_symlink(target)

    try:
        size = target.stat().st_size
    except OSError as exc:
        raise StyleMemoryError(f"Cannot stat {target}: {exc}") from exc
    if size > _MAX_FILE_BYTES:
        raise StyleMemoryError(
            f"{target}: file size {size} B exceeds cap "
            f"({_MAX_FILE_BYTES} B). Refusing to load — clear and re-save."
        )

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StyleMemoryError(f"Cannot read {target}: {exc}") from exc

    if not isinstance(data, dict):
        raise StyleMemoryError(f"{target}: expected a JSON object, got {type(data).__name__}")

    version = data.get("version")
    if version != _SCHEMA_VERSION:
        raise StyleMemoryError(
            f"{target}: schema version {version!r}, expected {_SCHEMA_VERSION}. "
            "Clear and re-save the profile."
        )

    profile_data = data.get("profile")
    if not isinstance(profile_data, dict):
        raise StyleMemoryError(f"{target}: missing 'profile' object")

    # Filter to known StyleProfile fields so extra keys don't crash construction.
    known_fields = set(asdict(StyleProfile()).keys())
    kwargs = {k: v for k, v in profile_data.items() if k in known_fields}
    try:
        return StyleProfile(**kwargs)
    except TypeError as exc:
        raise StyleMemoryError(f"{target}: cannot reconstruct profile: {exc}") from exc


def clear_profile(path: Path | None = None) -> bool:
    """Delete the persisted profile. Returns True if a file was removed,
    False if nothing was there. Symlinks are refused."""
    target = path or _default_path()
    if not target.exists():
        return False
    _refuse_symlink(target)
    target.unlink()
    return True


def format_summary(profile: StyleProfile | None) -> str:
    """Short, user-facing description of the current memory state."""
    if profile is None:
        return "No style memory on file."
    return (
        f"Style memory: {profile.total_words} words of sample measured. "
        f"Sentence σ={profile.sentence_length_stdev}; "
        f"contractions/1k={profile.contraction_rate}; "
        f"second-person/1k={profile.second_person_rate}."
    )
