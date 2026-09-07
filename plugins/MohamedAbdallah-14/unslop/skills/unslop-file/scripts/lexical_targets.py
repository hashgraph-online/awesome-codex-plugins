"""Stylometric target nudges for deterministic humanization.

This module compares a text against human baseline bands and applies a small
set of safe lexical edits. It does not invent first-person claims, facts, or
examples. When the gap requires judgment, it reports the gap and leaves the
text alone.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .stylometry import analyze

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BASELINE_PATH = _REPO_ROOT / "benchmarks" / "results" / "stylometric_baseline.json"


@dataclass(frozen=True)
class TargetGap:
    field: str
    current: float
    target_low: float
    target_high: float
    delta: float


def _normalize_baseline_payload(payload: object) -> dict[str, dict[str, float]]:
    if not isinstance(payload, dict):
        return {}
    fields = payload.get("fields", payload)
    out: dict[str, dict[str, float]] = {}
    if not isinstance(fields, dict):
        return out
    for field, stats in fields.items():
        if not isinstance(stats, dict):
            continue
        if "human_p25" not in stats or "human_p75" not in stats:
            continue
        try:
            out[field] = {
                "human_p25": float(stats["human_p25"]),
                "human_p75": float(stats["human_p75"]),
            }
        except (TypeError, ValueError):
            continue
    return out


def _load_package_baseline() -> dict[str, dict[str, float]]:
    """Try importlib.resources for the packaged baseline copy.

    Derives the package from __package__ so both source imports
    (unslop.scripts) and installed-wheel imports (scripts) resolve.
    """
    try:
        import importlib.resources as ir
        pkg = __package__ or "scripts"
        ref = ir.files(f"{pkg}.data").joinpath("stylometric_baseline.json")
        payload = json.loads(ref.read_text(encoding="utf-8"))
        return _normalize_baseline_payload(payload)
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        return {}


@lru_cache(maxsize=1)
def load_baselines(path: str | None = None) -> dict[str, dict[str, float]]:
    if path is not None:
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            parsed = _normalize_baseline_payload(payload)
            if parsed:
                return parsed
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    if _BASELINE_PATH.exists():
        try:
            payload = json.loads(_BASELINE_PATH.read_text(encoding="utf-8"))
            parsed = _normalize_baseline_payload(payload)
            if parsed:
                return parsed
        except (OSError, json.JSONDecodeError):
            pass

    pkg = _load_package_baseline()
    if pkg:
        return pkg

    sys.stderr.write(
        "unslop: stylometric baseline not found; anti-detector lexical "
        "targets disabled. Generate with: python3 benchmarks/"
        "stylometric_baseline.py\n"
    )
    return {}


def measure_gaps(
    text: str, baselines: dict[str, dict[str, float]] | None = None
) -> list[TargetGap]:
    profile = analyze(text)
    baseline = baselines or load_baselines()
    gaps: list[TargetGap] = []
    for field, stats in baseline.items():
        current = float(getattr(profile, field, 0.0))
        low = float(stats["human_p25"])
        high = float(stats["human_p75"])
        if current < low:
            delta = current - low
        elif current > high:
            delta = current - high
        else:
            continue
        gaps.append(TargetGap(field, current, low, high, delta))
    return sorted(gaps, key=lambda gap: abs(gap.delta), reverse=True)


_TOKEN_RE = re.compile(r"\b[A-Za-z']+\b")
_SLEEP_ON_RE = re.compile(
    r"\b(sleep|sleeps|slept|sit|sits|sat|rest|rests|rested|walk|walks|walked) "
    r"([a-z]+s)\b",
    re.IGNORECASE,
)

_LATINATE_REPLACEMENTS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\butilize\b", re.IGNORECASE), "use"),
    (re.compile(r"\butilizes\b", re.IGNORECASE), "uses"),
    (re.compile(r"\butilized\b", re.IGNORECASE), "used"),
    (re.compile(r"\butilizing\b", re.IGNORECASE), "using"),
    (re.compile(r"\bascertain\b", re.IGNORECASE), "figure out"),
    (re.compile(r"\bascertains\b", re.IGNORECASE), "figures out"),
    (re.compile(r"\bascertained\b", re.IGNORECASE), "figured out"),
    (re.compile(r"\bascertaining\b", re.IGNORECASE), "figuring out"),
    (re.compile(r"\bdemonstrate\b", re.IGNORECASE), "show"),
    (re.compile(r"\bdemonstrates\b", re.IGNORECASE), "shows"),
    (re.compile(r"\bdemonstrated\b", re.IGNORECASE), "showed"),
    (re.compile(r"\bdemonstrating\b", re.IGNORECASE), "showing"),
    (re.compile(r"\bfacilitate\b", re.IGNORECASE), "help"),
    (re.compile(r"\bfacilitates\b", re.IGNORECASE), "helps"),
    (re.compile(r"\bfacilitated\b", re.IGNORECASE), "helped"),
    (re.compile(r"\bfacilitating\b", re.IGNORECASE), "helping"),
    (re.compile(r"\bcommence\b", re.IGNORECASE), "start"),
    (re.compile(r"\bcommences\b", re.IGNORECASE), "starts"),
    (re.compile(r"\bcommenced\b", re.IGNORECASE), "started"),
    (re.compile(r"\bterminate\b", re.IGNORECASE), "end"),
    (re.compile(r"\bterminated\b", re.IGNORECASE), "ended"),
    (re.compile(r"\bsubsequently\b", re.IGNORECASE), "later"),
    (re.compile(r"\bapproximately\b", re.IGNORECASE), "about"),
    (re.compile(r"\bsufficient\b", re.IGNORECASE), "enough"),
    (re.compile(r"\binsufficient\b", re.IGNORECASE), "not enough"),
    (re.compile(r"\badditional\b", re.IGNORECASE), "more"),
    (re.compile(r"\bnumerous\b", re.IGNORECASE), "many"),
    (re.compile(r"\bobtain\b", re.IGNORECASE), "get"),
    (re.compile(r"\bobtained\b", re.IGNORECASE), "got"),
    (re.compile(r"\bassist\b", re.IGNORECASE), "help"),
    (re.compile(r"\bassisted\b", re.IGNORECASE), "helped"),
)

_CYCLING_GROUPS: tuple[tuple[str, ...], ...] = (
    ("showcase", "highlight", "emphasize", "underscore"),
    ("utilize", "leverage", "employ", "harness"),
)


def _has_gap(gaps: list[TargetGap], field: str, direction: str | None = None) -> bool:
    for gap in gaps:
        if gap.field != field:
            continue
        if direction == "low" and gap.delta < 0:
            return True
        if direction == "high" and gap.delta > 0:
            return True
        if direction is None:
            return True
    return False


def _cap_insertions(original: str) -> int:
    tokens = _TOKEN_RE.findall(original)
    return max(1, int(len(tokens) * 0.05)) if tokens else 0


def _inject_function_words(text: str) -> str:
    limit = _cap_insertions(text)
    if limit <= 0:
        return text
    state = {"insertions": 0}

    def repl(match: re.Match) -> str:
        if state["insertions"] >= limit:
            return match.group(0)
        state["insertions"] += 1
        return f"{match.group(1)} on {match.group(2)}"

    return _SLEEP_ON_RE.sub(repl, text)


def _replace_latinate(text: str) -> str:
    out = text
    for pattern, repl in _LATINATE_REPLACEMENTS:
        out = pattern.sub(repl, out)
    return out


def _dampen_synonym_cycling(text: str) -> str:
    def rewrite_paragraph(paragraph: str) -> str:
        out = paragraph
        lower = paragraph.lower()
        for group in _CYCLING_GROUPS:
            present = [word for word in group if re.search(rf"\b{word}\w*\b", lower)]
            if len(present) < 3:
                continue
            keeper = present[0]
            for word in present[1:]:
                out = re.sub(rf"\b{word}(?:s|ed|ing)?\b", keeper, out, flags=re.IGNORECASE)
        return out

    return "\n\n".join(rewrite_paragraph(p) for p in text.split("\n\n"))


def apply_targeted_pass(
    text: str,
    gaps: list[TargetGap],
    *,
    intensity: str = "balanced",
) -> str:
    if intensity == "subtle" or not gaps:
        return text

    from .humanize import _protect, _restore

    protected, table = _protect(text)

    if _has_gap(gaps, "latinate_ratio", "high") or intensity in ("balanced", "full", "anti-detector"):
        protected = _replace_latinate(protected)

    if intensity in ("full", "anti-detector"):
        if _has_gap(gaps, "function_word_rate", "low"):
            protected = _inject_function_words(protected)
        if _has_gap(gaps, "type_token_ratio", "high"):
            protected = _dampen_synonym_cycling(protected)

    return _restore(protected, table)
