"""HTML report generator for validated suggestion groups.

Generates interactive HTML reports from grouped.json data with
model badges, section context previews, and embedded log snippets.
Supports both grouped.json and consolidated.json as data sources.
"""

import base64
import hashlib
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple

try:
    from .stream_bootstrap import bootstrap_streams
    from .json_extractor import sanitize_model_name
    from .metrics import describe_usage
    from .judge_vocab import (
        JUDGE_AUTO_DECIDE,
        JUDGE_AUTO_DECIDE_SALVAGE,
        JUDGE_DECIDED,
        canonical_value,
        upgrade_legacy,
    )
except ImportError:
    # Direct script invocation (`python utils/html_report_generator.py`):
    # sys.path[0] is the utils/ directory, so import the sibling module directly.
    from stream_bootstrap import bootstrap_streams
    from json_extractor import sanitize_model_name
    from metrics import describe_usage
    from judge_vocab import (
        JUDGE_AUTO_DECIDE,
        JUDGE_AUTO_DECIDE_SALVAGE,
        JUDGE_DECIDED,
        canonical_value,
        upgrade_legacy,
    )

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model icon mapping — maps model families to OpenRouter icon data URIs
# ---------------------------------------------------------------------------

# Icons directory (SVGs downloaded from OpenRouter)
_ICONS_DIR = Path(__file__).parent.parent / "assets" / "icons"

# Cache of loaded icon data URIs
_icon_cache: Dict[str, str] = {}


def _load_icon_data_uri(filename: str) -> str:
    """Load an icon file (SVG or PNG) and return a data URI string."""
    if filename in _icon_cache:
        return _icon_cache[filename]
    icon_path = _ICONS_DIR / filename
    if icon_path.exists():
        raw = icon_path.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        mime = "image/svg+xml" if filename.endswith(".svg") else "image/png"
        uri = f"data:{mime};base64,{b64}"
    else:
        uri = ""
    _icon_cache[filename] = uri
    return uri


def _make_letter_icon_data_uri(letter: str, color: str) -> str:
    """Generate a simple SVG letter icon as a data URI."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="14" fill="{color}"/>'
        f'<text x="32" y="43" text-anchor="middle" font-family="system-ui,sans-serif" '
        f'font-size="36" font-weight="700" fill="white">{letter}</text></svg>'
    )
    b64 = base64.b64encode(svg.encode()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


# Mapping from icon key to (icon_filename_or_None, fallback_letter, fallback_color)
#
# Provenance rule (orca-harness-parity.md §6.2): Orca's MIT grant covers its
# copyright in the PNGs it bundles, NOT the third-party trademarks they depict.
# So Orca is used only as the *catalog* — which agent wears which mark — and each
# asset here is fetched from the vendor's own favicon/brand source, preferring
# SVG. A mark with no reachable first-party SVG gets the letter-icon fallback
# rather than a redrawn or re-hosted logo.
_ICON_DEFS: Dict[str, tuple] = {
    "anthropic":  ("Anthropic.svg", "A", "#CC9B7A"),
    "openai":     ("OpenAI.svg", "O", "#10A37F"),
    "google":     ("GoogleGemini.svg", "G", "#4285F4"),
    "xai":        ("xAI.svg", "X", "#1DA1F2"),
    "moonshotai": ("MoonshotAI.svg", "K", "#5C3DAA"),
    "zhipu":      ("Zhipu.png", "Z", "#3366FF"),
    "minimax":    ("MiniMax.png", "M", "#FF6633"),
    "cursor":     ("Cursor.svg", "C", "#1E1E1E"),
    "kilocode":   ("Kilocode.svg", "K", "#FF4444"),
    "opencode":   ("Opencode.svg", "O", "#333333"),
    "codex":      ("Codex.svg", "C", "#111111"),
    "nvidia":     ("Nvidia.svg", "N", "#77B900"),
    "qwen":       ("Qwen.svg", "Q", "#615CED"),
    # SVG sourced from mistral.ai/favicon.svg
    "mistral":    ("Mistral.svg", "M", "#FA520F"),
    # SVG sourced from block/goose:ui/desktop/src/images/icon.svg
    "goose":      ("Goose.svg", "G", "#0F172A"),
    # SVG sourced from pi.dev/favicon.svg
    "pi":         ("Pi.svg", "P", "#09090B"),
    # SVG sourced from Primer Octicons' copilot-16 icon (MIT)
    "copilot":    ("Copilot.svg", "C", "#24292F"),
    # SVG sourced from omp.sh/favicon.svg (oh-my-pi's own docs site)
    "omp":        ("OhMyPi.svg", "O", "#9B4DFF"),
    # No first-party SVG reachable — letter-icon fallback only
    "xiaomi":     (None, "M", "#FF6900"),
    "arcee":      (None, "T", "#3B82F6"),
    "vercel":     (None, "V", "#F45B25"),
    "deepseek":   (None, "D", "#4D6BFE"),
    "cline":      (None, "C", "#0EA5A4"),
    "aider":      (None, "A", "#14B8A6"),
    # Google Antigravity keeps its own key rather than borrowing "google": the
    # Gemini mark would mislabel the CLI as the model family it fans out to.
    "antigravity": (None, "A", "#4285F4"),
    # Orca's catalog has no mark for muse either — letter icon is the outcome,
    # not a placeholder waiting on a fetch.
    "muse":       (None, "M", "#7C3AED"),
}


# Provider (CLI tool) → icon key. Used to render a provider icon alongside
# the model's company icon when they differ.
_PROVIDER_ICON_KEYS: Dict[str, str] = {
    "claude-code":  "anthropic",
    "gemini":       "google",
    "codex":        "codex",
    "cursor-agent": "cursor",
    "kilocode":     "kilocode",
    "opencode":     "opencode",
    # Backfill: these ship today and had no provider-icon row, so the provider
    # column rendered nothing whenever the model name matched no family.
    "grok":         "xai",
    # Vercel fx is a CLI identity; model-family icons are resolved separately.
    "fx":           "vercel",
    "cline":        "cline",
    "goose":        "goose",
    "aider":        "aider",
    "agy":          "antigravity",
    "muse":         "muse",
    "pi":           "pi",
    # harness-expansion.md Wave 1/2 candidates. Keys are the frozen provider
    # keys of §8.1. Inert until the adapter registers — this dict is only ever
    # read through .get(), and no roster test cross-checks it against
    # _PROVIDERS — so a §6.3 demotion is a one-line delete here, not a bug.
    "copilot":      "copilot",
    "kimi":         "moonshotai",
    "qwen-code":    "qwen",
    "vibe":         "mistral",
    # oh-my-pi keeps its own key rather than borrowing "pi": omp fans out
    # across model families, so a borrowed mark would mislabel the CLI as one
    # of them — the same reason "antigravity" above is not "google".
    "omp":          "omp",
}


def _get_icon_data_uri(icon_key: str) -> str:
    """Get icon data URI for a given icon key."""
    if icon_key not in _ICON_DEFS:
        return ""
    svg_file, letter, color = _ICON_DEFS[icon_key]
    if svg_file:
        uri = _load_icon_data_uri(svg_file)
        if uri:
            return uri
    return _make_letter_icon_data_uri(letter, color)


def _resolve_model_icon_key(provider: str, model_name: str) -> str:
    """Determine the icon key for a provider:model combination.

    Maps the model name (and provider as fallback) to the underlying AI
    company whose icon should be displayed.
    """
    full = f"{provider}:{model_name}".lower()
    model_lower = model_name.lower()

    # Check model name patterns first (most specific)
    if any(k in model_lower for k in ("sonnet", "opus", "haiku", "claude")):
        return "anthropic"
    if any(k in model_lower for k in ("gpt", "codex", "o1", "o3", "o4")):
        return "openai"
    if "gemini" in model_lower:
        return "google"
    if "grok" in model_lower:
        return "xai"
    if any(k in full for k in ("kimi", "moonshot")):
        return "moonshotai"
    if any(k in full for k in ("glm", "z-ai", "zhipu")):
        return "zhipu"
    if "minimax" in full:
        return "minimax"
    if any(k in full for k in ("nemotron", "nvidia")):
        return "nvidia"
    if "qwen" in full:
        return "qwen"
    if "deepseek" in full:
        return "deepseek"
    if "mistral" in full:
        return "mistral"
    if any(k in full for k in ("mimo", "xiaomi")):
        return "xiaomi"
    if any(k in full for k in ("trinity", "arcee")):
        return "arcee"

    # Fall back to the provider's own icon when no model-family pattern matched
    return _PROVIDER_ICON_KEYS.get(provider.lower(), "")


def _resolve_provider_icon_key(provider: str) -> str:
    """Return the icon key for the invocation provider (CLI tool) itself."""
    return _PROVIDER_ICON_KEYS.get(provider.lower(), "")


# ---------------------------------------------------------------------------
# Canonical sort-order constants (single source of truth for the codebase)
# ---------------------------------------------------------------------------

VALIDATION_ORDER = {
    "needs-human-decision": 0,
    "valid": 1,
    "validation_failed": 2,
    "invalid": 3,
    "pending": 4,
}
UNKNOWN_STATUS_RANK = 5

IMPORTANCE_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "": 3}
UNKNOWN_IMPORTANCE_RANK = 3


# ---------------------------------------------------------------------------
# Shared sorting helpers
# ---------------------------------------------------------------------------

def compute_max_importance(suggestions: Optional[List[Dict[str, Any]]]) -> str:
    """Return the highest importance level among *suggestions*.

    Returns ``""`` when *suggestions* is ``None``, empty, or contains no
    recognised importance values — this maps to ``IMPORTANCE_ORDER[""]``
    (rank 3, after LOW) so that empty groups sort last within their
    validation-status tier.
    """
    if not suggestions:
        return ""
    best_rank = UNKNOWN_IMPORTANCE_RANK
    best_label = ""
    for s in suggestions:
        imp = (s.get("importance") or "").upper()
        rank = IMPORTANCE_ORDER.get(imp, UNKNOWN_IMPORTANCE_RANK)
        if rank < best_rank:
            best_rank = rank
            best_label = imp
    return best_label


def _sort_by_priority(
    items: List[Dict[str, Any]],
    status_fn: Callable[[Dict[str, Any]], str],
    importance_fn: Callable[[Dict[str, Any]], str],
) -> List[Dict[str, Any]]:
    """Generic priority sort.  Stamps ``originalIndex``, returns a new sorted list.

    Args:
        items: List of group dicts to sort.
        status_fn: Callable(item) -> str — extracts the validation status string.
        importance_fn: Callable(item) -> str — extracts the importance string.
    """
    for i, item in enumerate(items):
        if "originalIndex" not in item:
            item["originalIndex"] = i + 1
    def _key(item):
        return (
            VALIDATION_ORDER.get(status_fn(item), UNKNOWN_STATUS_RANK),
            IMPORTANCE_ORDER.get(importance_fn(item), UNKNOWN_IMPORTANCE_RANK),
            item.get("originalIndex", 0),
        )
    return sorted(items, key=_key)


def sort_groups_by_priority(
    groups: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Sort camelCase report-data dicts (post ``_build_group_data()``)."""
    return _sort_by_priority(
        groups,
        status_fn=lambda g: g.get("validationStatus", ""),
        importance_fn=lambda g: g.get("maxImportance", ""),
    )


def sort_raw_groups_by_priority(
    groups: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Sort raw snake_case grouped.json dicts."""
    return _sort_by_priority(
        groups,
        status_fn=lambda g: g.get("validation_status") or "",
        importance_fn=lambda g: compute_max_importance(g.get("suggestions", [])),
    )


def sort_consolidated_groups_by_priority(
    groups: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Sort consolidated group dicts (direct importance field, aggregate status)."""
    return _sort_by_priority(
        groups,
        status_fn=lambda g: g.get("validation_status") or "",
        importance_fn=lambda g: g.get("importance") or "",
    )


def derive_aggregate_validation_status(
    statuses: List[str],
) -> str:
    """Derive aggregate validation status from a list of constituent statuses.

    Selects the status with the **lowest** ``VALIDATION_ORDER`` rank (i.e.,
    highest priority wins).  Statuses not listed in ``VALIDATION_ORDER``
    receive ``UNKNOWN_STATUS_RANK`` and lose to all recognised statuses.

    Returns ``""`` when *statuses* is empty.
    """
    if not statuses:
        return ""
    # Use min() on rank — lowest rank = highest priority
    return min(
        statuses,
        key=lambda s: VALIDATION_ORDER.get(s, UNKNOWN_STATUS_RANK),
    )


def build_sort_config() -> Dict[str, Any]:
    """Build the ``sortConfig`` object for injection into HTML report data."""
    return {
        "validationOrder": VALIDATION_ORDER,
        "importanceOrder": IMPORTANCE_ORDER,
        "unknownStatusRank": UNKNOWN_STATUS_RANK,
        "unknownImportanceRank": UNKNOWN_IMPORTANCE_RANK,
    }


def hsl_to_hex(h: int, s: int, l: int) -> str:
    """Convert HSL values to hex color string.

    Args:
        h: Hue (0-360)
        s: Saturation (0-100)
        l: Lightness (0-100)

    Returns:
        Hex color string (e.g., "#B8860B")
    """
    s = s / 100
    l = l / 100

    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2

    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    r = int((r + m) * 255)
    g = int((g + m) * 255)
    b = int((b + m) * 255)

    return f"#{r:02X}{g:02X}{b:02X}"


def string_to_color(s: str) -> str:
    """Generate a consistent color from a string using hash.

    Uses HSL color space to produce visually distinct, pleasant colors.
    Same string always produces the same color.

    Args:
        s: Input string (e.g., model name "claude-3-opus")

    Returns:
        Hex color string (e.g., "#B8860B")
    """
    if not s:
        return "#6B7280"  # Default gray for empty string

    # Hash the string
    hash_bytes = hashlib.md5(s.encode()).digest()

    # Use first 3 bytes to generate HSL values
    # Hue: full 0-360 range
    hue = (hash_bytes[0] + hash_bytes[1] * 256) % 360

    # Saturation: 50-70% for good color visibility
    saturation = 50 + (hash_bytes[2] % 21)

    # Lightness: 45-55% for readability on both light/dark backgrounds
    lightness = 45 + (hash_bytes[3] % 11)

    # Convert HSL to RGB then to hex
    return hsl_to_hex(hue, saturation, lightness)


def parse_model_string(model_string: str) -> tuple[str, str]:
    """Parse a model string into provider and model name components.

    Handles formats like:
    - "anthropic:claude-3-opus" -> ("anthropic", "claude-3-opus")
    - "openai:gpt-4" -> ("openai", "gpt-4")
    - "claude-3-opus" -> ("", "claude-3-opus")

    Args:
        model_string: Full model identifier

    Returns:
        Tuple of (provider, model_name). Provider is empty string if not present.
    """
    if not model_string:
        return ("", "")

    if ":" in model_string:
        parts = model_string.split(":", 1)
        return (parts[0], parts[1])

    return ("", model_string)


def get_model_metadata(model_string: str) -> Dict[str, Any]:
    """Get color info for model badges using hash-based color generation.

    Generates separate consistent colors for provider and model name.
    Same provider always produces the same provider color.
    Same model name always produces the same model color.

    Args:
        model_string: Full model identifier (e.g., "anthropic:claude-3-opus", "gpt-4")

    Returns:
        Dict with:
        - 'full': The original model string
        - 'provider': Provider name (empty string if not present)
        - 'model': Model name
        - 'provider_color': Color for provider badge (gray if no provider)
        - 'model_color': Color for model badge
    """
    provider, model_name = parse_model_string(model_string)

    model_icon_key = _resolve_model_icon_key(provider, model_name)
    provider_icon_key = _resolve_provider_icon_key(provider)
    model_icon_uri = _get_icon_data_uri(model_icon_key) if model_icon_key else ""
    # Only emit the provider icon when it's distinct from the model icon —
    # avoids duplicate logos when the CLI and model are the same brand
    # (e.g. claude-code:opus, gemini:gemini-2.5-pro).
    provider_icon_uri = (
        _get_icon_data_uri(provider_icon_key)
        if provider_icon_key and provider_icon_key != model_icon_key
        else ""
    )

    return {
        "full": model_string,
        "provider": provider,
        "model": model_name,
        "provider_color": string_to_color(provider) if provider else "#6B7280",
        "model_color": string_to_color(model_name),
        "icon": model_icon_uri,
        "provider_icon": provider_icon_uri,
    }


def _attribution_notes(model: str, entry: Any) -> List[str]:
    """The provenance notes one ``served_models`` entry is worth, in order.

    Split out of :func:`served_model_label` so the usage clause can join the
    *same* parenthesis rather than opening a second one after it: a line
    reading ``model (served by X, fallback) ($0.04 est.)`` says the notes come
    from two unrelated systems, which is exactly backwards — they are two
    facts about one slot.
    """
    if not isinstance(entry, dict):
        return []
    notes: List[str] = []
    served = entry.get("served_model")
    # A primary that served its own turn is not an attribution note: it is the
    # model already printed at the head of the label.
    if served and served != model:
        notes.append(
            f"served by {served}, fallback" if entry.get("fallback")
            else f"served by {served}"
        )
    sandbox = entry.get("sandbox")
    if sandbox == "bypassed":
        notes.append(SANDBOX_BYPASSED_LABEL)
    elif isinstance(sandbox, str) and sandbox.startswith(SANDBOX_FALLBACK_WORD_PREFIX):
        notes.append(sandbox_fallback_label(sandbox))
    # A slot the plugin's jail failed (2026-09-30) keeps its rung on the record
    # (F1 item 6); its reason rides the same parenthesis.
    denied = jail_denied_label(entry)
    if denied:
        notes.append(denied)
    return notes


def served_model_label(
    model: str, served_models: Optional[Dict[str, Any]] = None
) -> str:
    """``model`` as a report label, carrying §3.6's served-model attribution.

    One renderer for every markdown surface that names a model *without* a
    cost beside it (the code review's per-issue ``**Model:**`` field, which
    repeats per finding and where a token count would be noise), so a fallback
    reads the same wherever it surfaces. Without an entry — which is every run
    under the shipped, empty ``fallback_models`` — the bare model string is
    returned and the report is byte-for-byte what it was. The summary lines
    that *do* name a cost use :func:`model_label`, which is this plus the
    usage clause in the same parenthesis.

    The D6 override's provenance (2026-09-17) renders on the same label:
    ``sandbox: "bypassed"`` in the entry appends ``ran unsandboxed:
    sandbox_fallback=auto``, so a report reader sees which slot's findings
    came from a model that ran with the operator's shell rights — beside the
    served-model note when both apply, alone when only one does. A slot on a
    **contained** fallback rung (``sandbox: "fallback-landlock"``, 2026-09-22)
    is not unsandboxed and never gets that label: it gets
    :func:`sandbox_fallback_label` instead, which names the rung.
    """
    notes = _attribution_notes(model, (served_models or {}).get(model))
    if not notes:
        return model
    return f"{model} ({'; '.join(notes)})"


def model_label(
    model: str,
    served_models: Optional[Dict[str, Any]] = None,
    usage: Optional[Dict[str, Any]] = None,
) -> str:
    """:func:`served_model_label` plus what the slot spent, in one parenthesis.

    The renderer for the summary lines that name each model once — the
    aggregate's ``**Models:**`` line in both lanes. ``usage`` is the fan-out's
    ``{model_spec: usage}`` map (``.status.json``'s ``usage`` key); a model
    with no entry renders exactly what it rendered before, which is the rule
    that keeps a report from a duration-only adapter free of ``$0.00``.

    ``describe_usage`` is the same clause the failed-slot error line and the
    HTML badge carry, imported rather than re-spelled: a report that quoted a
    cost in a second format would be a second answer to "what did this run
    cost", and the two would drift apart at the first rounding change.
    """
    notes = _attribution_notes(model, (served_models or {}).get(model))
    clause = describe_usage((usage or {}).get(model))
    if clause:
        notes.append(clause)
    if not notes:
        return model
    return f"{model} ({'; '.join(notes)})"


def sum_usage(usage: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Column-wise sum of a fan-out's per-model usage blocks, or ``{}``.

    What the run cost in total, which is the number an operator looks for
    first and the one no artifact carried before Stage U. Summed by key over
    whichever models reported, so a fan-out of one reporting adapter and two
    duration-only ones totals the one — the alternative, refusing to total a
    mixed run, would report nothing for the common case.

    **It is the run's total, not the badges' total.** The map handed in covers
    every slot that reported, including the ones that FAILED and therefore have
    no badge in this report at all, so the header figure can exceed the sum of
    what is displayed. That is the intended reading: the question is what the
    run cost, and the slot that burned a budget and returned nothing is the
    most expensive kind of answer there is.

    **Only numbers are added.** A usage block is an adapter's, and at least one
    adapter files a string in it (claude-code's ``served_model``, which rides
    the envelope its token counts came from). Anything that is not an ``int``
    or ``float`` is skipped rather than coerced, and ``bool`` is excluded
    because in Python it is an ``int`` and "1 tool use" is not what
    ``True`` meant. Float sums are rounded to six places: ``0.01 + 0.02``
    is ``0.030000000000000002`` in binary floating point, and a report
    header is not the place to show it.
    """
    totals: Dict[str, Any] = {}
    for entry in (usage or {}).values():
        if not isinstance(entry, dict):
            continue
        for key, value in entry.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            totals[key] = totals.get(key, 0) + value
    return {
        key: round(value, 6) if isinstance(value, float) else value
        for key, value in totals.items()
    }


#: The clause a failed model's entry carries when this attempt asked for a
#: salvage of it and the model is still failed. Fixed text on both lanes (the
#: live native request and the ``--exec-subagents`` unrecoverable one): the
#: subagent's own reason stays on its ``[SALVAGE_UNRECOVERABLE]`` stdout line,
#: so the header never quotes a second, paraphrased cause.
SALVAGE_REQUESTED_CLAUSE = "salvage requested, nothing recovered"

#: The label of the failure line, shared by ``report.md``'s bold header line and
#: the HTML warning notice built from the same text without the bold markers.
FAILED_MODELS_LABEL = "Models failed:"


def _one_line(text: Any) -> str:
    """*text* with every line break folded to a space.

    A stored failure reason is provider output and can carry a newline, which
    would end a markdown header line early — and in ``code-review``'s
    ``report.md`` a line that starts ``### N.`` after a blank one is an issue
    header the apply phase's parser reads a Skip box under. So the reason is
    verbatim apart from its line breaks.
    """
    return " ".join(str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"))


def failed_models_line(
    failed_models: Optional[Dict[str, Any]],
    requested_models: Optional[int] = None,
    salvage_requested: Optional[Sequence[str]] = None,
    *,
    bold: bool = True,
    served_models: Optional[Dict[str, Any]] = None,
) -> str:
    """The one-line account of the models that produced no result, or ``""``.

    ``**Models:**`` names only the models that produced results, so a reviewer
    that timed out used to be absent from every surface above the fold (plan
    review-run-scope-salvage-and-failure-visibility §5.2 item 2). This is the
    line that goes directly under it — and, with ``bold=False``, the HTML
    warning notice's ``message`` — so ``report.md`` and ``report.html`` are
    built from one string and cannot disagree::

        **Models failed:** 1 of 5 requested — pi:x/y: pi timed out after 1200s; salvage requested, nothing recovered

    Args:
        failed_models: ``{spec: reason}``; each reason is rendered verbatim
            (line breaks folded, see :func:`_one_line`). Empty or ``None``
            renders nothing.
        requested_models: The size of the requested set, never succeeded plus
            failed (a requested model with neither a result nor a recorded
            failure is in neither). ``None`` when the caller has no requested
            set, and the line then states the count without "of M".
        salvage_requested: The specs whose entry carries
            :data:`SALVAGE_REQUESTED_CLAUSE` — the caller's answer to "did this
            attempt ask for a salvage of this still-failed model"
            (``review_orchestrator_base.salvage_requested_models``).
        bold: ``True`` for the markdown header line, ``False`` for the notice.
        served_models: ``models_served`` (2026-09-30). A slot whose entry
            there carries ``failure_reason: jail-denied`` leads with ``denied
            by the plugin's jail: <path>`` — the record outlives the log that
            printed the ``[JAIL_DENIED]`` line (plan §6 F1 item 6) — and keeps
            its recorded reason after it (a later ``[CODEX_HOME_CHECK]`` or
            ``[MODE_CHECK]`` violation, code-review's ``(spent $X)``), unless
            that reason already carries the label.
    """
    if not failed_models:
        return ""
    salvaged = {str(spec) for spec in (salvage_requested or ())}
    entries = []
    for spec, reason in failed_models.items():
        # A record (2026-09-30: a jailed slot's `failure_reason: jail-denied`
        # plus its path) renders through the one reason renderer; a string is
        # itself, as before. The served record's jail label is prepended, never
        # substituted: the recorded reason can carry what happened after the
        # denial (a check violation, the spend clause).
        text = failure_reason_text(reason)
        denied = jail_denied_label((served_models or {}).get(spec))
        if denied and denied not in text:
            text = f"{denied}; {text}" if text.strip() else denied
        entry = f"{spec}: {_one_line(text)}"
        if str(spec) in salvaged:
            entry += f"; {SALVAGE_REQUESTED_CLAUSE}"
        entries.append(entry)
    count = len(failed_models)
    if requested_models is not None:
        count_text = f"{count} of {int(requested_models)} requested"
    else:
        count_text = str(count)
    label = f"**{FAILED_MODELS_LABEL}**" if bold else FAILED_MODELS_LABEL
    return f"{label} {count_text} — {'; '.join(entries)}"


def build_report_notices(
    notices: Optional[Sequence[Any]],
    failed_models: Optional[Dict[str, Any]] = None,
    requested_models: Optional[int] = None,
    salvage_requested: Optional[Sequence[str]] = None,
    served_models: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    """``reportData.notices``: the failure warning first, then *notices*.

    Every template's ``renderNotices`` prints ``escapeHtml(n.message)`` and
    nothing else, so a notice without a ``message`` renders as an empty
    coloured bar. Nothing reaches the list without a non-empty one — the
    data-source notices are filtered on the same rule — and the failure
    notice exists only when :func:`failed_models_line` has something to say.
    Shared by the phase report and the consolidated report so both pages
    carry the same bar.
    """
    result: List[Dict[str, str]] = []
    failure = failed_models_line(
        failed_models, requested_models, salvage_requested, bold=False,
        served_models=served_models,
    )
    if failure:
        result.append({"type": "warning", "message": failure})
    for notice in notices or ():
        if not isinstance(notice, dict):
            continue
        message = notice.get("message")
        if not isinstance(message, str) or not message.strip():
            continue
        result.append(notice)
    return result


#: The label a bypassed slot carries in every report surface. The config key
#: and its value are spelled out because they name the one setting that
#: decides this (and, by naming ``auto``, the word ``off`` that would have
#: kept the slot out), and the reader of a report is the person who should
#: know it.
SANDBOX_BYPASSED_LABEL = "ran unsandboxed: sandbox_fallback=auto"

#: The ``models_served`` word prefix for a slot on a **contained** fallback
#: rung (``fallback-landlock``) — ``llm_client.SANDBOX_FALLBACK_WORD_PREFIX``,
#: spelled here because this renderer reads recorded data and imports no
#: provider code.
SANDBOX_FALLBACK_WORD_PREFIX = "fallback-"


#: The recorded words of a slot on an **incidental**-grade rung, and the label
#: each renders as (plan codex-sandbox-unavailable-findings-and-fixes §7, "Step 2
#: subtask: messaging and markers", item 3; 2026-09-30). A closed set spelled
#: here, because this renderer reads recorded data and imports no provider
#: code: the plugin's Landlock jail stops stray writes and nothing more, so its
#: slot is never "sandboxed by fallback rung" — the label a real OS boundary
#: earns. A word outside this set keeps the contained wording, as before. The
#: label names no phase, so a read-only slot and a write dispatch share it.
INCIDENTAL_FALLBACK_LABELS: Dict[str, str] = {
    "fallback-plugin-landlock": (
        "stray writes stopped by plugin-landlock; not a boundary against the model"
    ),
}


def sandbox_fallback_label(word: str) -> str:
    """The report note for a slot on a fallback rung.

    A **contained** rung (``fallback-landlock``) says the slot was sandboxed —
    by a fallback boundary, named — because its findings came from a model
    whose writes the kernel denied, which is the opposite of what
    :data:`SANDBOX_BYPASSED_LABEL` tells a reader. An **incidental** rung
    (:data:`INCIDENTAL_FALLBACK_LABELS`, 2026-09-30) says what it stops and
    that it is not a boundary against the model, never "sandboxed".
    """
    incidental = INCIDENTAL_FALLBACK_LABELS.get(word)
    if incidental is not None:
        return incidental
    rung = word[len(SANDBOX_FALLBACK_WORD_PREFIX):] if word.startswith(
        SANDBOX_FALLBACK_WORD_PREFIX
    ) else word
    return f"sandboxed by fallback rung: {rung}"


#: The per-slot failure reason a jailed slot records when codex itself died on
#: an EACCES the plugin's jail caused (plan §6 F1 "Where it sits" item 6, "When
#: the jail denies a turn"), and the key carrying the denied path. Spelled here
#: for the same reason as :data:`INCIDENTAL_FALLBACK_LABELS`: the fan-out's
#: ``llm_client`` sets ``failure_reason: "jail-denied"`` on the slot's record,
#: and the report reads the record, never the provider code.
JAIL_DENIED_REASON = "jail-denied"
JAIL_DENIED_PATH_KEY = "jail_denied_path"
#: What the jail-denied label says when codex named no path (the probable-jail
#: class of ``landlock_dispatch.is_jail_failure``).
JAIL_DENIED_NO_PATH = "path not named"


def jail_denied_label(record: Any) -> Optional[str]:
    """``denied by the plugin's jail: <path>`` for a slot record whose
    ``failure_reason`` is ``jail-denied``, else ``None``.

    Generic over the record's shape: a ``failed_models`` value, a
    ``models_served`` entry or a ``progress.models`` row all carry the same two
    keys, so the report and ``status`` show the same words after the log that
    printed the ``[JAIL_DENIED]`` line is gone.
    """
    if not isinstance(record, Mapping):
        return None
    if record.get("failure_reason") != JAIL_DENIED_REASON:
        return None
    path = record.get(JAIL_DENIED_PATH_KEY)
    return f"denied by the plugin's jail: {path or JAIL_DENIED_NO_PATH}"


def failure_reason_text(reason: Any) -> str:
    """A ``failed_models`` value as the one reason a report line carries.

    A string is itself (every lane today). A record (2026-09-30) is its
    jail-denied label when it carries one, else its ``error``/``reason`` text —
    so a lane that starts recording a dict never renders as a Python repr.
    """
    if isinstance(reason, Mapping):
        label = jail_denied_label(reason)
        if label:
            return label
        text = reason.get("error") or reason.get("reason")
        return str(text) if text else "failed with no error recorded"
    return str(reason)


def extract_section_contexts(
    plan_content: str,
    section_refs: Set[str],
    full_section: bool = False
) -> Dict[str, str]:
    """Extract context around each referenced section header.

    Takes the plan markdown content and a set of section references
    (like "### Step 2") and returns surrounding context text for each.

    By default, extracts ~15 lines around each header (for tooltip/hover use).
    When full_section=True, extracts the full text from the matched ### header
    to the next ### header (or end of content), including any nested headers
    (e.g., #### within a ### section).

    Args:
        plan_content: The full markdown content of the plan
        section_refs: Set of section references to find (e.g., {"### Step 2"})
        full_section: If True, capture full section text between ### headers
            instead of ~15 lines around each header. Default False.

    Returns:
        Dict mapping section reference to surrounding context text
    """
    if not plan_content or not section_refs:
        return {}

    lines = plan_content.split('\n')
    contexts = {}

    for ref in section_refs:
        if not ref:
            continue

        # Find line index where this section header appears
        ref_lower = ref.lower().strip()
        found_idx = -1

        for i, line in enumerate(lines):
            line_stripped = line.strip().lower()
            # Match exact header or header that starts with ref
            if line_stripped == ref_lower or line_stripped.startswith(ref_lower):
                found_idx = i
                break

        if found_idx == -1:
            # Try partial match on the text after ### markers
            ref_text = ref.lstrip('#').strip().lower()
            for i, line in enumerate(lines):
                line_text = line.lstrip('#').strip().lower()
                if ref_text in line_text:
                    found_idx = i
                    break

        if found_idx >= 0:
            if full_section:
                # Determine the header level of the matched line
                matched_line = lines[found_idx].lstrip()
                header_level = 0
                for ch in matched_line:
                    if ch == '#':
                        header_level += 1
                    else:
                        break

                # Find the next header at the same or higher level (fewer or equal #'s)
                # Headers with more #'s (e.g., #### inside ###) are nested and included
                end_idx = len(lines)
                for j in range(found_idx + 1, len(lines)):
                    line_stripped = lines[j].lstrip()
                    if line_stripped.startswith('#'):
                        # Count the header level of this line
                        level = 0
                        for ch in line_stripped:
                            if ch == '#':
                                level += 1
                            else:
                                break
                        # A header at same or higher level ends the section
                        if 0 < level <= header_level:
                            end_idx = j
                            break

                context_lines = lines[found_idx:end_idx]
                # Strip trailing blank lines for cleaner output
                while context_lines and context_lines[-1].strip() == '':
                    context_lines.pop()
                contexts[ref] = '\n'.join(context_lines)
            else:
                # Extract ~15 lines of context (7 before, the line, 7 after)
                start = max(0, found_idx - 7)
                end = min(len(lines), found_idx + 8)
                context_lines = lines[start:end]
                contexts[ref] = '\n'.join(context_lines)

    return contexts


def extract_plan_section_order(plan_content: str) -> List[str]:
    """Return every section header of the plan, in the order it is written.

    This captures the plan's original narrative order so the HTML report can
    offer a "Plan Order" view alongside the priority-sorted view — and the
    report orders *whatever it buckets by*, so a heading the report can bucket
    under must appear here. Restricted to ``###``, it listed only the numbered
    task headings: a real 8-task review had six further buckets (Overview,
    Design Requirements, Implementation Tasks, File Changes, Testing,
    Priority) carrying 31 suggestion references between them, none of which
    the "natural" sort could place, so they fell to the arbitrary tail the
    template appends.

    ``##`` and deeper are the sections; a lone top-level ``#`` is the plan's
    title, and a section whose text is the whole document is not a section —
    so level 1 is used only by a plan that has no other heading level.
    Fenced code is skipped, because a shell comment is not a heading. Repeats
    are dropped, keeping the first, so the result is usable as a bucket key
    list.
    """
    if not plan_content:
        return []
    deep: List[str] = []
    top: List[str] = []
    fence = ""
    for line in plan_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not fence:
                fence = marker
            elif fence == marker:
                fence = ""
            continue
        if fence or not stripped.startswith("#"):
            continue
        level = len(stripped) - len(stripped.lstrip("#"))
        if level > 6 or not stripped[level:].startswith(" "):
            continue  # "#hashtag" and "####### deeper than markdown goes"
        (top if level == 1 else deep).append(stripped)
    order = deep or top
    seen: Set[str] = set()
    return [ref for ref in order if not (ref in seen or seen.add(ref))]


def embed_log_snippets(
    log_dir: Path,
    models: List[str],
    max_lines: int = 50
) -> Dict[str, str]:
    """Extract relevant portions of log files for each model.

    Looks for log_{model}.txt files in log_dir and returns
    the last max_lines of each log file.

    Args:
        log_dir: Directory containing log files
        models: List of model names to look for
        max_lines: Maximum number of lines to include (default 50)

    Returns:
        Dict mapping model name to log content (last max_lines)
    """
    log_snippets = {}

    if not log_dir.exists():
        return log_snippets

    for model in models:
        # Sanitize model name the same way the log files were actually named
        # (utils/json_extractor.sanitize_model_name), or a model with a dot in
        # it — e.g. "cursor-agent:composer-2.5" — never matches its own file.
        log_file = log_dir / f"log_{sanitize_model_name(model)}.txt"

        if not log_file.exists():
            # Try without sanitization
            log_file = log_dir / f"log_{model}.txt"

        if log_file.exists():
            try:
                content = log_file.read_text(encoding='utf-8', errors='replace')
                lines = content.split('\n')
                # Get last max_lines
                if len(lines) > max_lines:
                    lines = lines[-max_lines:]
                log_snippets[model] = '\n'.join(lines)
            except OSError:
                pass

    return log_snippets


def _build_suggestion_data(
    suggestion: Dict[str, Any],
    group_index: int,
    suggestion_index: int
) -> Dict[str, Any]:
    """Build the data structure for a single suggestion.

    Args:
        suggestion: Raw suggestion dict from grouped.json
        group_index: 1-based group index
        suggestion_index: 1-based suggestion index within group

    Returns:
        Formatted suggestion dict for report data
    """
    # Build file reference for code-review style suggestions
    file_path = suggestion.get("file", "")
    line_range = suggestion.get("line_range")
    file_ref = ""
    if file_path:
        file_ref = file_path
        if line_range and isinstance(line_range, (list, tuple)) and len(line_range) >= 2:
            file_ref += f":{line_range[0]}-{line_range[1]}"
        elif line_range and isinstance(line_range, (list, tuple)) and len(line_range) == 1:
            file_ref += f":{line_range[0]}"

    # Use stable content hash if available, fall back to positional ID
    suggestion_id = suggestion.get(
        "suggestion_hash", f"G{group_index}S{suggestion_index}"
    )

    result = {
        "id": suggestion_id,
        "title": suggestion.get("title", "Untitled"),
        "description": suggestion.get("desc", suggestion.get("description", "")),
        "importance": suggestion.get("importance", "MEDIUM").upper(),
        "type": suggestion.get("type", "unknown"),
        "sectionRef": suggestion.get("reference", suggestion.get("section", "")),
        "fileRef": file_ref,  # For code-review: file path with line range
        "model": suggestion.get("source_model", "unknown"),
        # PR-style contextual fields
        "anchorText": suggestion.get("anchor_text", None),
        "suggestedFix": suggestion.get("suggested_fix", None),
        "lineRange": suggestion.get("line_range", None),
    }

    # Add display label and display hash when available (Phase 1 stamps)
    display_label = suggestion.get("display_label")
    if display_label is not None:
        result["displayLabel"] = display_label
    display_hash = suggestion.get("display_hash")
    if display_hash is not None:
        result["displayHash"] = display_hash

    return result


def _build_group_data(
    group: Dict[str, Any],
    index: int,
    validation_results: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Build the data structure for a single group.

    Args:
        group: Raw group dict from grouped.json
        index: 0-based group index
        validation_results: Optional validation results list

    Returns:
        Formatted group dict for report data
    """
    # Get validation info from the group itself or from validation_results
    validation_status = group.get("validation_status")
    validation_reason = group.get("validation_reason", "")
    validation_confidence = group.get("validation_confidence", 0.0)

    # Try to get from validation_results if not in group
    if validation_results and index < len(validation_results):
        val_result = validation_results[index]
        if validation_status is None:
            validation_status = val_result.get("status")
        if not validation_reason:
            validation_reason = val_result.get("reason", "")
        if validation_confidence in (0.0, None):
            validation_confidence = val_result.get("confidence", 0.0)

    # Build suggestions list
    suggestions = []
    original_index = group.get("originalIndex", index + 1)
    raw_suggestions = group.get("suggestions", group.get("issues", []))
    for j, sugg in enumerate(raw_suggestions, start=1):
        suggestions.append(_build_suggestion_data(sugg, original_index, j))

    # Compute max importance from raw suggestions for sorting
    max_importance = compute_max_importance(raw_suggestions)

    result = {
        "index": index + 1,  # 1-based for display
        "originalIndex": group.get("originalIndex", index + 1),
        "theme": group.get("theme", "Unknown Theme"),
        "category": group.get("category", "unknown"),
        "models": group.get("models", []),
        "priorityScore": group.get("priority_score", 0),
        "validationStatus": validation_status or "pending",
        "validationReason": validation_reason,
        "validationConfidence": validation_confidence,
        "maxImportance": max_importance,
        "suggestions": suggestions,
    }

    # Add stable hash fields when available (Phase 1 stamps)
    group_hash = group.get("group_hash")
    if group_hash is not None:
        result["groupHash"] = group_hash
    display_label = group.get("display_label")
    if display_label is not None:
        result["displayLabel"] = display_label
    display_hash = group.get("display_hash")
    if display_hash is not None:
        result["displayHash"] = display_hash

    # A commit review's attribution (plans/review-commits.md §2.6): sibling
    # fields of the group, present only when the attribution pass ran, so a
    # plan's report data is unchanged.
    if "introduced_by_source" in group:
        result["introducedBy"] = group.get("introduced_by")
        result["introducedBySource"] = group.get("introduced_by_source")

    return result


# ---------------------------------------------------------------------------
# Consolidated.json support
# ---------------------------------------------------------------------------


def _validate_consolidated_schema(data: Any) -> bool:
    """Check whether *data* has the expected consolidated.json schema.

    Expected shapes:
    - Object with ``consolidated_groups`` key whose items contain
      ``underlying_group_ids`` and ``title``.
    - Top-level array of objects with ``underlying_group_ids``.
    """
    if isinstance(data, dict):
        groups = data.get("consolidated_groups")
        if not isinstance(groups, list):
            return False
        if len(groups) == 0:
            return True  # Empty is valid
        first = groups[0]
        return (
            isinstance(first, dict)
            and "underlying_group_ids" in first
            and "title" in first
        )
    if isinstance(data, list):
        if len(data) == 0:
            return True
        first = data[0]
        return isinstance(first, dict) and "underlying_group_ids" in first
    return False


def _load_consolidated_groups(
    consolidated_path: Path,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[Dict[str, Any]]]:
    """Load consolidated groups from *consolidated_path*.

    Returns ``(groups_list, metadata_dict)`` on success.
    Returns ``(None, None)`` if the file is missing or malformed.
    Logs a warning on malformed data.
    """
    if not consolidated_path.exists():
        return None, None
    try:
        raw = json.loads(consolidated_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "consolidated.json is malformed, falling back to grouped.json: %s", exc
        )
        return None, None

    if not _validate_consolidated_schema(raw):
        logger.warning(
            "consolidated.json is malformed, falling back to grouped.json"
        )
        return None, None

    if isinstance(raw, list):
        return raw, None
    # dict form
    return raw.get("consolidated_groups", []), raw.get("metadata")


def _build_grouped_lookup(
    groups: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Build a lookup table mapping group hashes/IDs to their group dicts.

    Looks at ``group_hash``, ``group_id``, ``groupHash`` (camelCase report
    data), and falls back to using the list index as a string key.
    """
    lookup: Dict[str, Dict[str, Any]] = {}
    for i, group in enumerate(groups):
        for key_field in ("group_hash", "group_id", "groupHash"):
            key = group.get(key_field)
            if key:
                lookup[key] = group
        # Also index by list position (string)
        lookup[str(i)] = group
    return lookup


def _resolve_underlying_groups(
    consolidated_group: Dict[str, Any],
    grouped_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Resolve ``underlying_group_ids`` to actual group dicts.

    Falls back to ``underlying_group_indices`` if ID resolution fails.
    Returns the resolved list (may be empty if resolution is impossible).
    """
    resolved: List[Dict[str, Any]] = []

    # Try underlying_group_ids first
    underlying_ids = consolidated_group.get("underlying_group_ids", [])
    for uid in underlying_ids:
        grp = grouped_lookup.get(uid)
        if grp is not None:
            resolved.append(grp)

    # If ID resolution yielded nothing, try index-based
    if not resolved:
        underlying_indices = consolidated_group.get("underlying_group_indices", [])
        for idx in underlying_indices:
            grp = grouped_lookup.get(str(idx))
            if grp is not None:
                resolved.append(grp)

    return resolved


def _expand_consolidated_into_groups(
    consolidated_groups: List[Dict[str, Any]],
    raw_groups: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Expand consolidated groups into underlying group dicts for rendering.

    Returns:
        (expanded_groups, umbrella_map)
        - expanded_groups: flat list of underlying group dicts (post
          ``_build_group_data()``) with consolidated metadata attached.
        - umbrella_map: maps underlying group hash to its consolidated
          group metadata (title, description, consolidated_id).
          Used by the template to render umbrella banners.
    """
    grouped_lookup = _build_grouped_lookup(raw_groups)
    expanded: List[Dict[str, Any]] = []
    umbrella_map: Dict[str, Dict[str, Any]] = {}
    seen_group_hashes: set = set()

    for cg in consolidated_groups:
        resolved = _resolve_underlying_groups(cg, grouped_lookup)
        consolidated_meta = {
            "consolidatedId": cg.get("consolidated_id", ""),
            "consolidatedTitle": cg.get("title", ""),
            "consolidatedDescription": cg.get("description", ""),
            "consolidatedImportance": cg.get("importance", ""),
            "consolidatedType": cg.get("type", ""),
            "isSingleton": cg.get("is_singleton", False),
            "displayIndex": cg.get("display_index", 0),
            "reasoning": cg.get("reasoning", ""),
        }

        if not resolved:
            # Cannot resolve underlying groups - create a flat card from
            # consolidated data directly
            flat_group = {
                "theme": cg.get("title", "Consolidated Suggestion"),
                "category": cg.get("type", "unknown"),
                "models": [],
                "validation_status": "",
                "suggestions": [{
                    "title": cg.get("title", ""),
                    "desc": cg.get("description", ""),
                    "importance": cg.get("importance", "MEDIUM"),
                    "type": cg.get("type", "modification"),
                    "reference": cg.get("reference", ""),
                    "source_model": "consolidated",
                }],
                "_consolidated_meta": consolidated_meta,
                "_is_consolidated_flat": True,
            }
            expanded.append(flat_group)
        else:
            # Tag each resolved group with consolidated metadata.
            # Use shallow copies to avoid mutating the original group dicts
            # from raw_groups (which are shared references via the lookup).
            first_in_umbrella = True
            for grp in resolved:
                grp_hash = grp.get("group_hash", grp.get("group_id", ""))
                if grp_hash and grp_hash in seen_group_hashes:
                    continue
                if grp_hash:
                    seen_group_hashes.add(grp_hash)

                # Shallow copy before attaching metadata so callers'
                # original group dicts are not mutated.
                grp_copy = {**grp}
                grp_copy["_consolidated_meta"] = consolidated_meta
                if first_in_umbrella:
                    grp_copy["_umbrella_first"] = True
                    first_in_umbrella = False

                # Map group hash to umbrella info for template rendering
                if grp_hash:
                    umbrella_map[grp_hash] = consolidated_meta

                expanded.append(grp_copy)

    return expanded, umbrella_map


def _load_data_source(
    phase_dir: Path,
    data_source: str,
    groups: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Dict[str, Any]]], List[Dict[str, str]]]:
    """Determine and load the data source for report generation.

    Args:
        phase_dir: Phase directory containing grouped.json / consolidated.json
        data_source: ``"auto"``, ``"consolidated"``, or ``"grouped"``
        groups: The groups already passed by the caller (from grouped.json)

    Returns:
        (effective_groups, umbrella_map, notices)
        - effective_groups: The groups to render (may be expanded from consolidated)
        - umbrella_map: Mapping of group hash -> consolidated metadata, or None
        - notices: List of notice dicts ``{"type": ..., "message": ...}``
    """
    notices: List[Dict[str, str]] = []

    if data_source == "grouped":
        return groups, None, notices

    consolidated_path = phase_dir / "consolidated.json"
    grouped_path = phase_dir / "grouped.json"

    if data_source == "consolidated":
        if not consolidated_path.exists():
            raise FileNotFoundError(
                f"consolidated.json not found at {consolidated_path}"
            )
        cons_groups, _meta = _load_consolidated_groups(consolidated_path)
        if cons_groups is None:
            raise ValueError(
                f"consolidated.json at {consolidated_path} is malformed"
            )
        expanded, umbrella_map = _expand_consolidated_into_groups(
            cons_groups, groups
        )
        return expanded, umbrella_map, notices

    # data_source == "auto"
    if consolidated_path.exists():
        cons_groups, _meta = _load_consolidated_groups(consolidated_path)
        if cons_groups is not None:
            expanded, umbrella_map = _expand_consolidated_into_groups(
                cons_groups, groups
            )
            return expanded, umbrella_map, notices
        else:
            # Malformed consolidated.json - fall back
            notices.append({
                "type": "warning",
                "message": (
                    "Report generated from grouped data \u2014 "
                    "consolidated data was unavailable"
                ),
            })
            return groups, None, notices

    # No consolidated.json - use grouped data
    return groups, None, notices


def _parse_tasks_markdown(content: str) -> Dict[str, Any]:
    """Parse a tasks.md markdown file into a metadata dict keyed by task ref.

    The tasks.md format uses headers like ``### Task T001: Create base config``
    followed by metadata lines (Dependencies, Files, Complexity) and body text.

    Returns a dict mapping the full section ref (e.g.
    ``"### Task T001: Create base config"``) to a metadata dict with keys:
    ``task_id``, ``title``, ``dependencies``, ``files``, ``complexity``,
    ``description``.
    """
    # Match task headers: ## Task T001: ... or ### Task T001: ...
    header_pattern = re.compile(
        r'^(#{2,3}\s+(?:Task\s+)?T\d+[^:\n]*(?::\s*.*)?)', re.MULTILINE
    )
    headers = list(header_pattern.finditer(content))
    if not headers:
        return {}

    result: Dict[str, Any] = {}
    for i, match in enumerate(headers):
        header_text = match.group(1).strip()
        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
        body = content[start:end].strip()

        # Extract task ID (e.g. "T001")
        tid_match = re.search(r'(T\d+)', header_text)
        task_id = tid_match.group(1) if tid_match else ""

        # Extract title (text after "Task T001:" or "T001:")
        title_match = re.search(r'T\d+[^:]*:\s*(.*)', header_text)
        title = title_match.group(1).strip() if title_match else header_text

        # Extract structured metadata from body lines
        deps = ""
        files = ""
        complexity = ""
        desc_lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("**dependencies**"):
                deps = re.sub(r'\*\*Dependencies\*\*\s*:\s*', '', stripped, flags=re.IGNORECASE).strip()
            elif stripped.lower().startswith("**files"):
                files = re.sub(r'\*\*Files[^*]*\*\*\s*:\s*', '', stripped, flags=re.IGNORECASE).strip()
            elif stripped.lower().startswith("**complexity**"):
                complexity = re.sub(r'\*\*Complexity\*\*\s*:\s*', '', stripped, flags=re.IGNORECASE).strip()
            elif stripped and not stripped.startswith("---"):
                desc_lines.append(stripped)

        meta: Dict[str, Any] = {
            "task_id": task_id,
            "title": title,
            "dependencies": deps,
            "files": files,
            "complexity": complexity,
            "description": "\n".join(desc_lines[:5]),  # First 5 lines
        }

        # Key by the full header text to match sectionRef values
        result[header_text] = meta
        # Also key by bare task ID for fallback matching
        if task_id:
            result[task_id] = meta

    return result


def generate_html_report(
    groups: List[Dict[str, Any]],
    plan_path: Path,
    phase_dir: Path,
    phase_type: str,
    models: List[str],
    failed_models: Optional[Dict[str, str]] = None,
    validation_results: Optional[List[Dict[str, Any]]] = None,
    base_ref: Optional[str] = None,
    tasks_path: Optional[Path] = None,
    template_style: str = 'pr',
    diff_data: Optional[Dict] = None,
    data_source: str = 'auto',
    file_snapshots: Optional[Dict[str, list]] = None,
    served_models: Optional[Dict[str, Dict[str, Any]]] = None,
    usage: Optional[Dict[str, Dict[str, Any]]] = None,
    commit_review: Optional[Mapping[str, Any]] = None,
    requested_models: Optional[int] = None,
    salvage_requested: Optional[Sequence[str]] = None,
    head_ref: Optional[str] = None,
    repo_root: Optional[str] = None,
    file_labels: Optional[Dict[str, str]] = None,
) -> str:
    """Generate complete HTML report and return the HTML string.

    Args:
        groups: Validated groups from grouped.json
        plan_path: Path to the original plan file
        phase_dir: Directory for this phase (for log files)
        phase_type: Phase identifier ("review-plan", "code-review", "review-tasks")
        models: List of models that were used
        failed_models: Optional dict of model name -> error message for
            failures. Written out as ``reportData.failedModels`` (always a
            dict; the templates iterate it with ``Object.keys``), and, when
            non-empty, as one ``warning`` notice whose ``message`` is
            :func:`failed_models_line` without its bold markers — the same
            text as ``report.md``'s ``**Models failed:**`` line.
        requested_models: The size of the run's requested model set, written
            out as ``reportData.requestedModels`` and used for the notice's
            "N of M requested". The caller's own count (the fan-out's
            ``len(model_specs)``, a reaggregate's recorded requested set) —
            never succeeded plus failed. ``None`` leaves the key out, and the
            page then names the failures without "of M".
        salvage_requested: The failed specs whose entry carries the salvage
            clause, exactly as the caller passed them to the markdown line.
        validation_results: Optional list of validation results
        base_ref: Optional git ref to diff against for PR-style code context.
            When provided (and ``diff_data`` is ``None``), ``capture_diff_hunks()``
            is called to obtain structured diff data for files referenced by
            suggestions.
        tasks_path: Optional path to a tasks JSON file.  When provided, task
            metadata is loaded and passed to ``build_task_view()``.
        template_style: Template to use — ``'pr'`` selects
            ``pr_report_template.html`` (default), ``'flat'`` selects the
            original ``report_template.html``.
        diff_data: Optional pre-computed diff hunk data (as returned by
            ``capture_diff_hunks()``).  When provided, it is used directly as
            ``reportData.diffData``, bypassing ``base_ref``-driven capture.
            This allows callers like ``reaggregate_from_existing_files()`` to
            inject cached diff data without re-running the git operation.
        data_source: Data source strategy — ``"auto"`` (default) checks for
            ``consolidated.json`` first, falls back to ``grouped.json``;
            ``"consolidated"`` uses ``consolidated.json`` directly (raises
            if missing); ``"grouped"`` uses ``grouped.json`` directly.
        file_snapshots: Optional dict mapping file paths to pre-captured
            line lists (as returned by ``capture_file_snapshots()``).  When
            provided, ``capture_file_context()`` uses these snapshots instead
            of reading files from disk, ensuring the report reflects file
            state at review start rather than at report-generation time.
        served_models: Optional §3.6 attribution, ``{model_spec: {"served_model":
            str, "fallback": bool}}``.  Only ever non-empty when a
            ``fallback_models`` list is configured; an entry labels that model's
            badge with the model that actually served the turn and adds
            ``reportData.servedModels``.  Omitted (the shipped default) leaves
            ``report_data.json`` and the embedded data exactly as they were.
        usage: Optional per-model usage, ``{model_spec: {"input_tokens", ...,
            "cost_usd", "tool_uses"}}``, as the fan-out recorded it in
            ``.status.json``.  Non-empty only for adapters that report usage at
            all (``usage_support`` above ``none``) — a model with no entry gets
            no ``usage`` key on its metadata and no clause on its badge, which
            is what keeps a duration-only adapter from being reported as a free
            run.  Adds ``reportData.usageTotal`` (the columnwise sum over the
            models that reported) and its rendered label.
        commit_review: A commit review's report payload
            (``utils.commit_report.report_payload``, plans/review-commits.md
            §2.10): stored as ``reportData.commitRange`` with the attribution
            per group, so the header's commit block, the commit filter, the
            "Introduced by" lines, the drift badges and the export help's
            apply command render from ``report_data.json`` alone (a
            regenerated report calls no git). ``None`` adds nothing.
        head_ref: The commit a pinned review ends at (``review-code
            --head-ref``, a commit brief; plans/review-commits.md §2.5). The
            diff hunks are then ``capture_diff_hunks(base_ref, files,
            head_ref, cwd=repo_root)`` — two commits, no "uncommitted changes"
            notice — the snapshots default to the files as that commit holds
            them (``capture_file_snapshots_at``), and the context chain never
            reads the disk for a file missing from the snapshots (a path absent
            at ``head``): the diff data (a deleted file's
            ``last_known_content``), then ``anchor_text``, then nothing, so a
            file recreated on disk since ``head`` never shows working-tree
            bytes as the reviewed code. ``None`` keeps today's chain.
        repo_root: Where those git reads run (the paths are root-relative).
        file_labels: ``{path: label}`` for the paths absent at ``head``
            (``deleted in <range>``, ``renamed to <new> in <range>``, ``absent
            at <head7>``), carried on the file's ``fileContexts`` entry as
            ``label``, the same words the validation excerpt's header uses.

    Returns:
        Complete HTML string for the report

    Raises:
        FileNotFoundError: When ``data_source="consolidated"`` and the file
            does not exist.
        ValueError: When ``data_source`` is not one of the allowed values,
            or when ``data_source="consolidated"`` and the file is malformed.
    """
    if data_source not in ("auto", "consolidated", "grouped"):
        raise ValueError(
            f"data_source must be 'auto', 'consolidated', or 'grouped', "
            f"got {data_source!r}"
        )

    # --- Resolve data source (consolidated vs grouped) ---
    effective_groups, umbrella_map, source_notices = _load_data_source(
        phase_dir, data_source, groups
    )

    # Select template based on template_style
    templates_dir = Path(__file__).parent.parent / 'templates'
    if template_style == 'pr':
        template_path = templates_dir / 'pr_report_template.html'
        if not template_path.exists():
            import warnings
            warnings.warn(
                f"PR template not found at {template_path}, falling back to flat template"
            )
            template_path = templates_dir / 'report_template.html'
    else:
        template_path = templates_dir / 'report_template.html'

    if not template_path.exists():
        # Return a basic error HTML if template is missing
        return f"""<!DOCTYPE html>
<html>
<head><title>Report Error</title></head>
<body>
<h1>Error: Template Not Found</h1>
<p>Could not find template at: {template_path}</p>
<p>Please ensure the template file exists.</p>
</body>
</html>"""

    template = template_path.read_text(encoding='utf-8')

    # Gather all section references from suggestions. A composite reference
    # is split into the sections it names: those are the sectionView's bucket
    # keys, and the whole composite string matches no header in the plan, so
    # collecting it unsplit left every one of them without context.
    section_refs: Set[str] = set()
    for group in effective_groups:
        for sugg in group.get("suggestions", group.get("issues", [])):
            ref = sugg.get("reference", sugg.get("section", ""))
            section_refs.update(split_section_refs(ref))

    # Read plan content for section contexts
    plan_content = ""
    if plan_path.exists():
        try:
            plan_content = plan_path.read_text(encoding='utf-8')
        except OSError:
            pass

    # Extract section contexts for hover previews
    section_contexts = extract_section_contexts(plan_content, section_refs)

    # Get log snippets
    log_snippets = embed_log_snippets(phase_dir, models)

    # Build groups data
    groups_data = []
    for i, group in enumerate(effective_groups):
        built = _build_group_data(group, i, validation_results)
        # Carry through consolidated metadata if present
        cons_meta = group.get("_consolidated_meta")
        if cons_meta is not None:
            built["_consolidatedMeta"] = cons_meta
        if group.get("_umbrella_first"):
            built["_umbrellaFirst"] = True
        if group.get("_is_consolidated_flat"):
            built["_isConsolidatedFlat"] = True
        groups_data.append(built)

    # Sort groups by priority (validation status, then importance, then original index)
    groups_data = sort_groups_by_priority(groups_data)

    # Build model metadata for badges
    model_metadata = {}
    for model in models:
        model_metadata[model] = get_model_metadata(model)
        # §3.6: a report must never attribute a fallback model's output to the
        # primary. The badge text is `metadata.model` in every template, so the
        # served model is folded into it there rather than in three templates —
        # and only when a fallback really fired, so an unconfigured run's badge
        # (and its persisted report_data.json) is unchanged.
        served_entry = (served_models or {}).get(model)
        if isinstance(served_entry, dict) and served_entry.get("served_model"):
            served = served_entry["served_model"]
            model_metadata[model]["served_model"] = served
            model_metadata[model]["fallback"] = bool(served_entry.get("fallback"))
            if served_entry.get("fallback"):
                model_metadata[model]["model"] = (
                    f"{model_metadata[model]['model']} (fallback: {served})"
                )
        # D6 override (2026-09-17): the same badge names a slot that ran with
        # no sandbox, so the HTML report says it wherever the markdown does.
        if isinstance(served_entry, dict) and served_entry.get("sandbox") == "bypassed":
            model_metadata[model]["sandbox"] = "bypassed"
            model_metadata[model]["model"] = (
                f"{model_metadata[model]['model']} (unsandboxed)"
            )
        # Landlock rung (2026-09-22): a contained fallback rung is a sandbox,
        # so the badge names the rung and never says "unsandboxed".
        elif isinstance(served_entry, dict) and str(
            served_entry.get("sandbox") or ""
        ).startswith(SANDBOX_FALLBACK_WORD_PREFIX):
            word = served_entry["sandbox"]
            model_metadata[model]["sandbox"] = word
            model_metadata[model]["model"] = (
                f"{model_metadata[model]['model']} ({sandbox_fallback_label(word)})"
            )
        # Stage U: what this slot spent, on the same metadata dict the badge is
        # rendered from — the numbers for anything that wants to compute, and
        # the rendered clause beside them because the *text* is settled here
        # rather than in three templates. The templates then print a string
        # instead of each carrying its own copy of "cost to the cent, drop it
        # under half a cent, say est., thousands separators on the token count"
        # — the rule that would drift three ways the first time it changed.
        # `describe_usage` is the same function the failed-slot error line and
        # the markdown `**Models:**` line call, so the three say the same words.
        # Absent when the adapter reported nothing, never `{}` or `$0.00`.
        model_usage = (usage or {}).get(model)
        if isinstance(model_usage, dict) and model_usage:
            model_metadata[model]["usage"] = model_usage
            label = describe_usage(model_usage)
            if label:
                model_metadata[model]["usage_label"] = label

    # Extract plan title from markdown (first # heading), fallback to filename
    plan_title = ""
    for line in plan_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            plan_title = stripped[2:].strip()
            break
    if not plan_title:
        plan_title = plan_path.stem

    # --- PR-style view indexes ---
    file_view = build_file_view(groups_data)
    section_view = build_section_view(groups_data)

    # Load task metadata if tasks_path provided.
    # Supports both JSON (tasks.json) and markdown (tasks.md) formats.
    tasks_metadata: Optional[Dict[str, Any]] = None
    if tasks_path is not None:
        try:
            raw_text = tasks_path.read_text(encoding='utf-8')
            if tasks_path.suffix == '.json':
                tasks_metadata = json.loads(raw_text)
            elif tasks_path.suffix == '.md':
                tasks_metadata = _parse_tasks_markdown(raw_text)
            else:
                # Try JSON first, fall back to markdown parsing
                try:
                    tasks_metadata = json.loads(raw_text)
                except json.JSONDecodeError:
                    tasks_metadata = _parse_tasks_markdown(raw_text)
        except OSError as exc:
            logger.warning("Could not load tasks metadata from %s: %s", tasks_path, exc)
            tasks_metadata = None

    task_view = build_task_view(groups_data, tasks_metadata)

    # --- Diff data: pre-computed takes precedence over base_ref capture ---
    # Normalize empty string base_ref to None so we don't attempt a
    # diff capture with an invalid (empty) ref.
    if not base_ref:
        base_ref = None
    # Collect file paths referenced by suggestions
    referenced_files: List[str] = []
    seen_files: Set[str] = set()
    for group in groups_data:
        for sugg in group.get("suggestions", []):
            file_ref = sugg.get("fileRef", "")
            fpath = _extract_file_path(file_ref)
            if fpath and fpath not in seen_files:
                seen_files.add(fpath)
                referenced_files.append(fpath)
    resolved_diff_data: Optional[Dict[str, Any]] = None
    if diff_data is not None:
        # Use pre-computed diff data directly
        resolved_diff_data = diff_data
    elif base_ref is not None:
        if referenced_files:
            try:
                from .git_utils import capture_diff_hunks
                if head_ref is None:
                    resolved_diff_data = capture_diff_hunks(base_ref, referenced_files)
                else:
                    resolved_diff_data = capture_diff_hunks(
                        base_ref, referenced_files, head_ref=head_ref, cwd=repo_root,
                    )
            except Exception as exc:
                import warnings
                warnings.warn(f"Failed to capture diff hunks: {exc}")
                resolved_diff_data = None

    # A pinned review's context is the reviewed code: the files as `head`
    # holds them, read once here unless the caller handed snapshots in.
    if head_ref is not None and file_snapshots is None and referenced_files:
        try:
            from .git_utils import capture_file_snapshots_at
            file_snapshots = capture_file_snapshots_at(
                head_ref, referenced_files, cwd=repo_root,
            )
        except Exception as exc:
            import warnings
            warnings.warn(f"Failed to read files at {head_ref[:12]}: {exc}")
            file_snapshots = {}

    def _file_context(
        fpath: str, line_range: List[int], context_lines: int = 5,
    ) -> Optional[List[Dict[str, Any]]]:
        """``capture_file_context``, which never falls back to the disk on a
        pinned review: a path missing from the head snapshots has no file
        context there (it is absent at `head`), whatever the disk holds."""
        if head_ref is not None and (not file_snapshots or fpath not in file_snapshots):
            return None
        from .git_utils import capture_file_context
        return capture_file_context(
            fpath, line_range, context_lines=context_lines,
            file_snapshots=file_snapshots,
        )

    # --- File contexts fallback chain ---
    # For each file referenced by suggestions, try:
    # 1. diff hunks (already in resolved_diff_data)
    # 2. file content via capture_file_context()
    # 3. anchor_text from the suggestion itself
    file_contexts: Dict[str, Any] = {}
    for group in groups_data:
        for sugg in group.get("suggestions", []):
            file_ref = sugg.get("fileRef", "")
            fpath = _extract_file_path(file_ref)
            if not fpath or fpath in file_contexts:
                continue

            # Check if diff data already covers this file
            if resolved_diff_data and fpath in resolved_diff_data:
                file_contexts[fpath] = {"source": "diff", "available": True}
                continue

            # Try file content fallback
            line_range = sugg.get("lineRange")
            if line_range and isinstance(line_range, (list, tuple)) and len(line_range) >= 1:
                try:
                    ctx = _file_context(fpath, list(line_range))
                    if ctx is not None:
                        file_contexts[fpath] = {
                            "source": "file",
                            "lines": ctx,
                            "available": True,
                        }
                        continue
                except Exception:
                    pass

            # Final fallback: anchor_text
            anchor = sugg.get("anchorText")
            if anchor:
                file_contexts[fpath] = {
                    "source": "anchor",
                    "anchorText": anchor,
                    "available": True,
                }
            else:
                file_contexts[fpath] = {
                    "source": "none",
                    "available": False,
                }

    # --- Augment file contexts with lines for ALL suggestion lineRanges ---
    # The loop above only captures context for the first suggestion per file.
    # For files with diff data, outside-diff suggestions have no context lines.
    # This second pass captures file content covering all suggestion lineRanges
    # so the template can render context around outside-diff suggestions.
    file_line_ranges: Dict[str, List[List[int]]] = {}
    for group in groups_data:
        for sugg in group.get("suggestions", []):
            file_ref = sugg.get("fileRef", "")
            fpath = _extract_file_path(file_ref)
            line_range = sugg.get("lineRange")
            if (
                fpath
                and line_range
                and isinstance(line_range, (list, tuple))
                and len(line_range) >= 1
            ):
                file_line_ranges.setdefault(fpath, []).append(list(line_range))

    for fpath, ranges in file_line_ranges.items():
        entry = file_contexts.get(fpath, {})
        # Skip if we already have context lines
        if entry.get("lines"):
            continue
        # Merge all ranges into one broad range — the template filters
        # to ±5 lines around each specific suggestion's lineRange.
        all_starts = [r[0] for r in ranges]
        all_ends = [r[1] if len(r) > 1 else r[0] for r in ranges]
        merged_range = [min(all_starts), max(all_ends)]
        try:
            ctx = _file_context(fpath, merged_range, context_lines=5)
            if ctx is not None:
                if fpath in file_contexts:
                    file_contexts[fpath]["lines"] = ctx
                else:
                    file_contexts[fpath] = {
                        "source": "file",
                        "lines": ctx,
                        "available": True,
                    }
        except Exception:
            pass

    # A path absent at `head` says why in its context's header: the same words
    # as its validation excerpt (plans/review-commits.md §2.5).
    for fpath, label in (file_labels or {}).items():
        if fpath in file_contexts and label:
            file_contexts[fpath]["label"] = label

    # --- Plan section ordering (narrative order from markdown) ---
    section_order = extract_plan_section_order(plan_content)

    # --- Full section contexts for sectionView ---
    # Extract for ALL section_order headers + suggestion refs so every
    # plan section has rendered content in the PR view.
    all_section_refs: Set[str] = set(section_order)
    all_section_refs.update(section_refs)
    full_section_contexts: Dict[str, str] = {}
    if all_section_refs:
        full_section_contexts = extract_section_contexts(
            plan_content, all_section_refs, full_section=True
        )

    # --- Merge all plan sections into sectionView ---
    # Ensure every section from section_order appears in section_view,
    # even if it has no suggestions. This enables the "full document" PR view.
    def _normalize_section_ref(ref: str) -> str:
        """Strip leading # and lowercase for fuzzy matching."""
        return ref.lstrip('#').strip().lower()

    def _find_canonical_match(
        ref: str, canonical_map: Dict[str, str]
    ) -> Optional[str]:
        """Find a canonical sectionView key matching a section_order ref."""
        norm = _normalize_section_ref(ref)
        # Exact match
        if norm in canonical_map:
            return canonical_map[norm]
        # Starts-with fallback (handles truncated refs)
        for canon_norm, canon_key in canonical_map.items():
            if canon_norm.startswith(norm) or norm.startswith(canon_norm):
                return canon_key
        return None

    # Build normalized map of existing sectionView keys
    sv_canonical: Dict[str, str] = {}  # normalized -> original key
    for sv_key in section_view:
        sv_canonical[_normalize_section_ref(sv_key)] = sv_key

    # Merge sectionView keys that match section_order entries,
    # and inject empty entries for sections not already in sectionView.
    for so_ref in section_order:
        match = _find_canonical_match(so_ref, sv_canonical)
        if match is None:
            # Section has no suggestions - inject empty entry
            section_view[so_ref] = {
                "suggestions": [],
                "suggestionCount": 0,
                "maxImportance": "",
                "hasSuggestions": False,
            }
        else:
            # Mark existing entry as having suggestions
            section_view[match]["hasSuggestions"] = True

    # Ensure hasSuggestions is set on ALL entries
    for key in section_view:
        if "hasSuggestions" not in section_view[key]:
            has = len(section_view[key].get("suggestions", [])) > 0
            section_view[key]["hasSuggestions"] = has

    # --- Merge all tasks into taskView ---
    # If tasks_metadata is available, ensure every task appears in task_view.
    if tasks_metadata:
        # Extract bare task IDs (T001, T002, etc.) to avoid duplicates
        existing_task_ids: Set[str] = set()
        for tk in task_view:
            if tk.startswith('_'):
                continue
            # Normalize: extract T\d+ pattern
            m = re.match(r'(T\d+)', tk)
            if m:
                existing_task_ids.add(m.group(1))
            else:
                existing_task_ids.add(tk)

        for task_id, meta in tasks_metadata.items():
            # _parse_tasks_markdown keys every task under BOTH the bare ID
            # and the full header text ("### Task T001: ...") pointing at
            # the identical meta dict, so the bare-ID key alone already
            # covers every task. Skip the header-text key here: a bare
            # `re.match(r'(T\d+)', task_id)` never matches it (the string
            # doesn't start with "T"), which used to fall through to the
            # `else` branch and back-fill a second, empty entry keyed by
            # the whole header.
            if not re.fullmatch(r'T\d+', task_id):
                continue
            if task_id not in existing_task_ids:
                task_view[task_id] = {
                    "taskMetadata": meta,
                    "suggestions": [],
                    "suggestionCount": 0,
                    "maxImportance": "",
                    "hasSuggestions": False,
                }
                existing_task_ids.add(task_id)

    # Ensure hasSuggestions is set on ALL task entries
    for key in task_view:
        if key.startswith('_'):
            continue
        if "hasSuggestions" not in task_view[key]:
            has = len(task_view[key].get("suggestions", [])) > 0
            task_view[key]["hasSuggestions"] = has

    # --- Global suggestions: those without file or section anchors ---
    global_suggestions_list: List[Dict[str, Any]] = []
    global_entry = file_view.get("_global", {})
    for grp in global_entry.get("suggestions", []):
        global_suggestions_list.extend(grp.get("suggestions", []))

    # Build the complete report data
    report_data = {
        "planPath": str(plan_path),
        "planTitle": plan_title,
        "title": plan_title,
        "baseRef": base_ref,
        "phase": phase_type,
        # Intentionally False for all phases — the review-tasks phase now
        # supports skip/override actions, so interactive controls are enabled
        # everywhere.  See review_orchestrator_base.py aggregate_results().
        "readOnly": False,
        "generatedAt": datetime.now().isoformat(),
        "models": models,
        "modelMetadata": model_metadata,
        "failedModels": failed_models or {},
        "sortConfig": build_sort_config(),
        "groups": groups_data,
        "sectionContexts": section_contexts,
        "logSnippets": log_snippets,
        # PR-style view indexes
        "fileView": file_view,
        "sectionView": section_view,
        "taskView": task_view,
        "globalSuggestions": global_suggestions_list,
        "fullSectionContexts": full_section_contexts,
        "sectionOrder": section_order,
        "notices": build_report_notices(
            source_notices, failed_models, requested_models, salvage_requested,
            served_models=served_models,
        ),
        "summary": {
            "totalGroups": len(effective_groups),
            "totalSuggestions": sum(
                len(g.get("suggestions", g.get("issues", [])))
                for g in effective_groups
            ),
            "validCount": sum(
                1 for g in groups_data
                if g["validationStatus"] == "valid"
            ),
            "invalidCount": sum(
                1 for g in groups_data
                if g["validationStatus"] == "invalid"
            ),
            "needsHumanCount": sum(
                1 for g in groups_data
                if g["validationStatus"] == "needs-human-decision"
            ),
            "validationFailedCount": sum(
                1 for g in groups_data
                if g["validationStatus"] == "validation_failed"
            ),
        }
    }

    # The denominator of "N of M requested", as the caller counted it. Absent
    # rather than guessed when the caller holds no requested set: succeeded
    # plus failed would silently drop a requested model that has neither a
    # result nor a recorded failure.
    if requested_models is not None:
        report_data["requestedModels"] = int(requested_models)

    # §3.6: the structured half of the attribution, added only when a fallback
    # list was configured AND something came back — so a default run's
    # report_data.json gains no key at all.
    if served_models:
        report_data["servedModels"] = served_models

    # Stage U, the same rule: the run total is added only when some adapter
    # reported something, so a fan-out of duration-only adapters leaves
    # `report_data.json` exactly as it was — no `usageTotal`, no `$0.00` in the
    # header. The label travels beside the numbers for the same reason the
    # per-model one does: the templates render text, not a formatting rule.
    usage_total = sum_usage(usage)
    if usage_total:
        report_data["usageTotal"] = usage_total
        total_label = describe_usage(usage_total)
        if total_label:
            report_data["usageTotalLabel"] = total_label

    # A commit review's header, filter, badges and export help (§2.10).
    if commit_review:
        report_data[COMMIT_RANGE_KEY] = commit_range_report_data(commit_review, groups_data)

    # Conditionally add diff data and file contexts
    if resolved_diff_data is not None:
        report_data["diffData"] = resolved_diff_data
    if file_contexts:
        report_data["fileContexts"] = file_contexts

    # Add consolidated metadata when using consolidated data source
    if umbrella_map is not None:
        report_data["umbrellaMap"] = umbrella_map
        report_data["dataSource"] = "consolidated"
    else:
        report_data["dataSource"] = "grouped"

    # Record the template style so a later post-apply regeneration
    # (regenerate_report_with_human_decisions) re-renders with the same template.
    report_data["templateStyle"] = template_style

    html = _embed_report_data(report_data, template)

    # Persist the assembled report_data so the apply phase can overlay human
    # decisions onto it and re-embed without reconstructing runtime inputs
    # (diff_data, base_ref, models, ...). Best-effort: never fail report
    # generation if the sidecar cannot be written.
    try:
        (phase_dir / "report_data.json").write_text(
            json.dumps(report_data, indent=2), encoding="utf-8"
        )
    except OSError:
        pass

    return html


#: ``report_data.json``'s key for a commit review's payload.
COMMIT_RANGE_KEY = "commitRange"

#: The apply commands the flat report's export help names for a plan's review
#: (every review phase shares that template). A commit review passes its own
#: list (``commitRange.applyCommands``) instead, plans/review-commits.md §2.10.
DEFAULT_APPLY_COMMANDS: Tuple[str, ...] = (
    "apply-suggestions", "apply-code-fixes", "apply-task-suggestions",
)

#: The label the flat report's header gives the anchor document of a plan's
#: review; a commit review passes ``commitRange.documentLabel`` (§2.8).
DEFAULT_DOCUMENT_LABEL = "Plan"

#: Template slots the generator fills before the data goes in. Each is an
#: HTML comment, so a template read without the generator renders nothing.
SLOT_DOCUMENT_LABEL = "<!--MLLM:document-label-->"
SLOT_APPLY_COMMANDS = "<!--MLLM:apply-commands-->"
SLOT_EXPORT_HELP = "<!--MLLM:export-help-->"


def commit_range_report_data(
    commit_review: Mapping[str, Any], groups_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """``reportData.commitRange``: the payload plus the attribution per group
    (``{groupHash: {introducedBy, source}}``). Each group's data also gains
    the attributed commit's short SHA and subject, read from the payload's
    ``commits`` (every commit of the range), never from git."""
    subjects = {
        str(c.get("sha")): c for c in commit_review.get("commits") or ()
        if isinstance(c, Mapping)
    }
    attribution: Dict[str, Dict[str, Any]] = {}
    for group in groups_data:
        if "introducedBySource" not in group:
            continue
        sha = group.get("introducedBy")
        if sha:
            group["introducedByShort"] = str(sha)[:7]
            group["introducedBySubject"] = str((subjects.get(sha) or {}).get("subject") or "")
        if group.get("groupHash"):
            attribution[str(group["groupHash"])] = {
                "introducedBy": sha, "source": group.get("introducedBySource"),
            }
    data = dict(commit_review)
    data["attribution"] = attribution
    return data


def _join_commands(commands: Sequence[str]) -> str:
    """``a``, ``a or b``, ``a, b, or c``: the export help's wording."""
    items = [str(c) for c in commands if c]
    if len(items) <= 1:
        return items[0] if items else ""
    if len(items) == 2:
        return f"{items[0]} or {items[1]}"
    return ", ".join(items[:-1]) + f", or {items[-1]}"


def _fill_template_slots(template: str, report_data: Mapping[str, Any]) -> str:
    """Fill the label and export-help slots from *report_data*.

    A plan's review gets exactly the text the templates used to carry
    (``Plan:``, the three apply commands, no PR-template help); a commit
    review gets ``Commit brief:`` and its own apply command, from the payload
    the generator stored, so a regenerated report says the same."""
    import html as _html

    commit = report_data.get(COMMIT_RANGE_KEY)
    commit = commit if isinstance(commit, Mapping) else None
    label = (commit or {}).get("documentLabel") or DEFAULT_DOCUMENT_LABEL
    commands = list((commit or {}).get("applyCommands") or DEFAULT_APPLY_COMMANDS)
    joined = _html.escape(_join_commands(commands), quote=False)
    help_html = ""
    if commit:
        help_html = (
            '<span class="export-help" id="export-help">Export saves '
            '<code>user_selections.json</code>: put it next to <code>report.md</code>, '
            f'then run <code>{joined}</code> to apply what you kept.</span>'
        )
    return (
        template
        .replace(SLOT_DOCUMENT_LABEL, _html.escape(f"{label}:", quote=False))
        .replace(SLOT_APPLY_COMMANDS, joined)
        .replace(SLOT_EXPORT_HELP, help_html)
    )


def _embed_report_data(report_data: Dict[str, Any], template: str) -> str:
    """Embed ``report_data`` as JSON into ``template`` at the data placeholder.

    Shared by initial generation and post-apply regeneration so both paths
    escape and inject the data identically. The template's slots
    (:func:`_fill_template_slots`) are filled first, before any data is in
    it, so text inside the data can never be taken for a slot.
    """
    template = _fill_template_slots(template, report_data)
    # Escape sequences that would break out of the surrounding <script> tag:
    #   </script>, </ in general, and <!-- (HTML comment opener inside JS).
    # \/ is valid JSON (RFC 8259 §7), so this stays parseable.
    json_data = (
        json.dumps(report_data, indent=2)
        .replace("</", "<\\/")
        .replace("<!--", "<\\!--")
    )

    # Replace the placeholder in the template
    # The template has: const reportData = /* REPORT_DATA_PLACEHOLDER */null;
    # We replace the entire "/* ... */null" pattern with the actual JSON data
    if "/* REPORT_DATA_PLACEHOLDER */null" in template:
        return template.replace("/* REPORT_DATA_PLACEHOLDER */null", json_data)
    elif "/* REPORT_DATA_PLACEHOLDER */" in template:
        return template.replace("/* REPORT_DATA_PLACEHOLDER */", json_data)
    elif "REPORT_DATA_PLACEHOLDER" in template:
        return template.replace("REPORT_DATA_PLACEHOLDER", json_data)
    else:
        # Fallback: inject before </body>
        inject_script = f"""
<script>
const reportData = {json_data};
// Initialize report if renderReport function exists
if (typeof renderReport === 'function') {{
    renderReport(reportData);
}}
</script>
"""
        return template.replace("</body>", f"{inject_script}</body>")


def write_html_report(html: str, phase_dir: Path) -> Path:
    """Write HTML report to the phase directory.

    Args:
        html: The complete HTML content to write
        phase_dir: Directory to write the report to

    Returns:
        Path to the written report file
    """
    phase_dir.mkdir(parents=True, exist_ok=True)
    report_path = phase_dir / "report.html"
    report_path.write_text(html, encoding='utf-8')
    return report_path


# ---------------------------------------------------------------------------
# PR-style view index builders
# ---------------------------------------------------------------------------

def _extract_file_path(file_ref: str) -> str:
    """Extract the file path from a fileRef string, stripping line ranges.

    Examples:
        "src/auth/login.py:43-50" -> "src/auth/login.py"
        "src/auth/login.py:43" -> "src/auth/login.py"
        "src/auth/login.py" -> "src/auth/login.py"
        "" -> ""
    """
    if not file_ref:
        return ""
    # Strip trailing :line or :line-line
    idx = file_ref.rfind(":")
    if idx > 0:
        after_colon = file_ref[idx + 1:]
        # Only strip if the part after the colon looks like a line range
        if after_colon and all(c in "0123456789-" for c in after_colon):
            return file_ref[:idx]
    return file_ref


def _get_group_file_path(group: Dict[str, Any]) -> str:
    """Determine the primary file path for a group.

    Uses the first non-empty ``fileRef`` among the group's suggestions.
    Returns ``""`` if no suggestion has a ``fileRef``.
    """
    for suggestion in group.get("suggestions", []):
        file_ref = suggestion.get("fileRef", "")
        if file_ref:
            return _extract_file_path(file_ref)
    return ""


#: A reviewer that cites two places writes one composite reference —
#: ``"## Design Requirements / ### 7. Lap Integration"``, occasionally
#: comma-joined. Split on a *delimited* separator only: a bare slash is part
#: of a heading (``### 5. Visual/Audio Effects (Juice)``) and splitting there
#: would invent two sections that the plan does not have.
_SECTION_REF_SEPARATOR = re.compile(r"\s+/\s+|,\s+")


def split_section_refs(section_ref: str) -> List[str]:
    """Split a composite section reference into the sections it names.

    ``"## Design Requirements / ### 7. Lap Integration"`` names two sections;
    a plain ``"### 7. Lap Integration"`` names one. Order is preserved and
    repeats are dropped, so a reference can be used directly as a bucket key
    list.
    """
    if not section_ref:
        return []
    refs: List[str] = []
    seen: Set[str] = set()
    for part in _SECTION_REF_SEPARATOR.split(str(section_ref)):
        part = part.strip()
        if part and part not in seen:
            seen.add(part)
            refs.append(part)
    return refs


def _get_group_section_refs(group: Dict[str, Any]) -> List[str]:
    """Every section a group's suggestions cite, deduped, in first-seen order.

    A group is counted under *each* section it names rather than under the
    whole reference string. Bucketing by the raw string made every composite
    reference its own bucket — a real 8-section plan review rendered 23
    section buckets, and the section a composite named second was invisible
    in the one that carried its name.

    Returns ``[]`` if no suggestion has a ``sectionRef``.
    """
    refs: List[str] = []
    seen: Set[str] = set()
    for suggestion in group.get("suggestions", []):
        for ref in split_section_refs(suggestion.get("sectionRef", "")):
            if ref not in seen:
                seen.add(ref)
                refs.append(ref)
    return refs


def _get_group_task_refs(group: Dict[str, Any]) -> List[str]:
    """Every task a group's suggestions cite, deduped, in first-seen order.

    Task review stores the task ID in the ``sectionRef`` / ``reference``
    field (which maps to ``sectionRef`` in camelCase report data), and a
    suggestion that spans two tasks writes both. Returns ``[]`` if no
    suggestion has a ``sectionRef``.
    """
    return _get_group_section_refs(group)


def _collect_all_suggestions(groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten all suggestions from a list of groups into a single list."""
    result = []
    for group in groups:
        result.extend(group.get("suggestions", []))
    return result


def _file_sort_key(file_path: str) -> tuple:
    """Sort key for file paths: directory first, then filename alphabetically.

    Sorts by (directory, filename) so files in the same directory are
    grouped together, and within each directory files are sorted
    alphabetically.  The ``_global`` key always sorts last.
    """
    if file_path == "_global":
        # Sort _global last
        return ("\xff", "\xff")
    parts = file_path.rsplit("/", 1)
    if len(parts) == 2:
        return (parts[0].lower(), parts[1].lower())
    # No directory component — sort at root level
    return ("", parts[0].lower())


def build_file_view(
    groups: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a file-based index from the flat groups list.

    Groups suggestions by ``fileRef`` file path for code-review PR view.
    Suggestions with no ``fileRef`` are placed under the ``_global`` key.

    Args:
        groups: List of processed group dicts (post ``_build_group_data()``).

    Returns:
        Dict mapping file paths (and ``_global``) to::

            {
                "suggestions": [group, ...],  # groups anchored to this file
                "suggestionCount": int,        # total individual suggestions
                "maxImportance": str,          # highest importance across all suggestions
            }

        Keys are sorted by directory then alphabetically, with ``_global`` last.
    """
    file_buckets: Dict[str, List[Dict[str, Any]]] = {}

    for group in groups:
        file_path = _get_group_file_path(group)
        key = file_path if file_path else "_global"
        file_buckets.setdefault(key, []).append(group)

    # Build the result dict with sorted keys
    sorted_keys = sorted(file_buckets.keys(), key=_file_sort_key)

    result: Dict[str, Any] = {}
    for key in sorted_keys:
        bucket_groups = file_buckets[key]
        all_suggestions = _collect_all_suggestions(bucket_groups)
        result[key] = {
            "suggestions": bucket_groups,
            "suggestionCount": len(all_suggestions),
            "maxImportance": compute_max_importance(all_suggestions),
        }

    # Ensure _global key exists even if empty
    if "_global" not in result:
        result["_global"] = {
            "suggestions": [],
            "suggestionCount": 0,
            "maxImportance": "",
        }

    return result


def build_section_view(
    groups: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a section-based index from the flat groups list.

    Groups suggestions by ``sectionRef`` for plan-review PR view. A composite
    reference (``"## Overview / ### 7. Lap Integration"``) is split, and the
    group is counted under **each** section it names — so a section's bucket
    holds everything that cited it, however the citing reviewer spelled the
    citation. Groups with no ``sectionRef`` are placed under the ``_global``
    key.

    A group naming two sections appears in two buckets, so the bucket counts
    sum to more than the group count. That is the point: the view answers
    "what did reviewers say about this section?", and a suggestion about two
    sections is an answer for both.

    Args:
        groups: List of processed group dicts (post ``_build_group_data()``).

    Returns:
        Dict mapping section references (and ``_global``) to::

            {
                "suggestions": [group, ...],  # groups anchored to this section
                "suggestionCount": int,        # total individual suggestions
                "maxImportance": str,          # highest importance across all suggestions
            }
    """
    section_buckets: Dict[str, List[Dict[str, Any]]] = {}

    for group in groups:
        for key in _get_group_section_refs(group) or ["_global"]:
            section_buckets.setdefault(key, []).append(group)

    result: Dict[str, Any] = {}
    for key, bucket_groups in section_buckets.items():
        all_suggestions = _collect_all_suggestions(bucket_groups)
        result[key] = {
            "suggestions": bucket_groups,
            "suggestionCount": len(all_suggestions),
            "maxImportance": compute_max_importance(all_suggestions),
        }

    return result


def build_task_view(
    groups: List[Dict[str, Any]],
    tasks_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a task-based index from the flat groups list.

    Groups suggestions by task ID (from the ``sectionRef`` / ``reference``
    field) for task-review PR view.  A composite reference naming more than
    one task (``"T003 / T004"``, ``"T003, T004"``) is split and the group is
    counted under each task it names.  A reference that isn't a bare task
    ID (``"Plan Coverage"``, or a plan section heading like
    ``"## 4.6 Timing & Checkpoints"`` — ``prompts/task_review.txt`` invites
    either spelling for a coverage-gap finding) is routed to the
    ``_coverageGaps`` bucket instead of becoming its own phantom task — a
    composite naming a non-task reference alongside a real task lands in
    both. Groups with no reference at all go to the ``_unanchored`` bucket.

    Args:
        groups: List of processed group dicts (post ``_build_group_data()``).
        tasks_metadata: Optional dict mapping task IDs (e.g. ``"T001"``)
            to task metadata dicts.  When ``None``, all ``taskMetadata``
            values in the result are ``None``.

    Returns:
        Dict mapping task IDs (and ``_coverageGaps``, ``_unanchored``) to::

            {
                "taskMetadata": {...} | None,
                "suggestions": [group, ...],
                "suggestionCount": int,
                "maxImportance": str,
            }

        The ``_coverageGaps`` entry contains groups whose reference is not
        a bare task ID (``"Plan Coverage"`` or a plan section heading).
        The ``_unanchored`` entry contains groups with no reference.
    """
    task_buckets: Dict[str, List[Dict[str, Any]]] = {}
    coverage_gaps: List[Dict[str, Any]] = []
    unanchored: List[Dict[str, Any]] = []

    for group in groups:
        task_refs = _get_group_task_refs(group)
        if not task_refs:
            # Groups with no reference — unanchored findings
            unanchored.append(group)
            continue
        for task_ref in task_refs:
            # Anything that isn't a bare "T###" id is a coverage-gap
            # reference, not a task — the prompt spells those either as
            # the literal "Plan Coverage" or as a plan section heading
            # (e.g. "## 4.6 Timing & Checkpoints"), and treating the
            # literal string as the only such spelling turned every
            # heading-style coverage gap into its own phantom task.
            if not re.fullmatch(r'T\d+', task_ref):
                coverage_gaps.append(group)
            else:
                task_buckets.setdefault(task_ref, []).append(group)

    result: Dict[str, Any] = {}

    for task_id, bucket_groups in task_buckets.items():
        all_suggestions = _collect_all_suggestions(bucket_groups)
        task_meta = None
        if tasks_metadata is not None:
            task_meta = tasks_metadata.get(task_id, None)
        result[task_id] = {
            "taskMetadata": task_meta,
            "suggestions": bucket_groups,
            "suggestionCount": len(all_suggestions),
            "maxImportance": compute_max_importance(all_suggestions),
        }

    # Always include _coverageGaps
    coverage_suggestions = _collect_all_suggestions(coverage_gaps)
    result["_coverageGaps"] = {
        "suggestions": coverage_gaps,
        "suggestionCount": len(coverage_suggestions),
        "maxImportance": compute_max_importance(coverage_suggestions),
    }

    # Always include _unanchored (groups with no reference)
    unanchored_suggestions = _collect_all_suggestions(unanchored)
    result["_unanchored"] = {
        "suggestions": unanchored,
        "suggestionCount": len(unanchored_suggestions),
        "maxImportance": compute_max_importance(unanchored_suggestions),
    }

    return result


# ---------------------------------------------------------------------------
# Post-apply human-decision overlay
# ---------------------------------------------------------------------------

def _normalize_human_decision(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a state.json human-decision record for the report template.

    Maps the recorded shape (``decision`` plus ``batch_context`` markers) into
    the camelCase fields the template's ``getHumanDecisionInfo()`` reads,
    collapsing everything to a single ``outcome`` of approved / salvaged /
    skipped. A salvaged item is recorded with ``decision == "approved"`` and a
    ``judge_auto_decide_salvage`` marker, so the marker — not ``decision`` —
    determines the outcome. A record in the ``claude_*`` spelling an earlier
    version wrote is read through ``judge_vocab.canonical_value``, so it renders
    the same and the sidecar it is written back to carries only the new names.
    """
    bc = record.get("batch_context") or {}
    decision_source = canonical_value(bc.get("decision_source"))
    batch_action = canonical_value(bc.get("batch_action"))
    source = decision_source or batch_action or "user"
    decision = record.get("decision")
    is_salvage = JUDGE_AUTO_DECIDE_SALVAGE in (decision_source, batch_action)
    if is_salvage:
        outcome = "salvaged"
    elif decision == "approved":
        outcome = "approved"
    elif decision == "skipped":
        outcome = "skipped"
    else:
        outcome = decision or "decided"
    return {
        "outcome": outcome,
        "decision": decision,
        JUDGE_DECIDED: str(source).startswith(JUDGE_AUTO_DECIDE),
        "source": source,
        "reason": record.get("reason", "") or "",
        "salvagedDescription": bc.get("salvaged_description", "") or "",
        "dropped": bc.get("dropped", "") or "",
        "importanceAtDecision": bc.get("importance_at_decision", "") or "",
        "judge": bc.get("judge", "") or "",
    }


def _overlay_human_decisions(
    report_data: Dict[str, Any],
    human_decisions: Dict[str, Dict[str, Any]],
) -> int:
    """Attach normalized human decisions onto ``report_data`` groups in place.

    Decisions are keyed by group_id (== ``group_hash``), matched against each
    group's ``groupHash``. Returns the number of groups matched and stamps a
    ``humanDecisionsSummary`` onto ``report_data``.

    The overlay is a **replacement**, not an accumulation: any stamp a previous
    overlay left on a group that this decision map does not name is dropped
    first. The sidecar is rewritten with what this function produced, so keeping
    them would survive `--fresh` (which clears ``human_decisions_{phase}``) and
    show two judging rounds' badges at once, under a
    ``humanDecisionsSummary`` that counted only the newer round.
    """
    summary = {
        "approved": 0,
        "salvaged": 0,
        "skipped": 0,
        JUDGE_DECIDED: 0,
        "total": 0,
    }
    matched = 0
    for group in report_data.get("groups", []):
        group_hash = group.get("groupHash")
        group.pop("humanDecision", None)
        if not group_hash or group_hash not in human_decisions:
            continue
        info = _normalize_human_decision(human_decisions[group_hash])
        group["humanDecision"] = info
        matched += 1
        summary["total"] += 1
        if info["outcome"] in summary:
            summary[info["outcome"]] += 1
        if info[JUDGE_DECIDED]:
            summary[JUDGE_DECIDED] += 1
    report_data["humanDecisionsSummary"] = summary
    return matched


def _load_report_template(template_style: str) -> str:
    """Load the report template text for the given style ('pr' or 'flat')."""
    templates_dir = Path(__file__).parent.parent / "templates"
    if template_style == "pr":
        template_path = templates_dir / "pr_report_template.html"
        if not template_path.exists():
            template_path = templates_dir / "report_template.html"
    else:
        template_path = templates_dir / "report_template.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Report template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def _overlay_guard_skips(report_data: Dict[str, Any], guard: Optional[Dict[str, Any]]) -> int:
    """Badge each group the commit apply guard skipped (plans/review-commits.md
    §2.7, §2.10): ``guardSkip: {reason, files, label}`` on the group, where
    the label reads "skipped: file changed since ``<head7>``" or "skipped:
    context plan". A replacement, like the decision overlay: a stamp from an
    earlier overlay that this guard does not name is dropped. Returns the
    number of groups stamped."""
    skipped = (guard or {}).get("skipped") or {}
    head = str((guard or {}).get("head") or "")
    stamped = 0
    for group in report_data.get("groups", []):
        group.pop("guardSkip", None)
        entry = skipped.get(group.get("groupHash") or "")
        if not isinstance(entry, dict):
            continue
        reason = str(entry.get("reason") or "")
        label = ("skipped: context plan" if reason == "context_plan"
                 else f"skipped: file changed since {head[:7]}")
        group["guardSkip"] = {
            "reason": reason,
            "files": [str(f) for f in entry.get("files") or []],
            "label": label,
        }
        stamped += 1
    return stamped


def regenerate_report_with_human_decisions(
    phase_dir: Path,
    human_decisions: Dict[str, Dict[str, Any]],
    template_style: Optional[str] = None,
    *,
    guard: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[Path], int]:
    """Re-render ``{phase_dir}/report.html`` with human decisions overlaid.

    Loads the ``report_data.json`` sidecar (persisted at review time), overlays
    the supplied human decisions (keyed by ``group_hash``), and re-embeds into
    the template — no reconstruction of the original runtime inputs
    (diff_data, base_ref, models, ...).

    Returns ``(report_path, matched)`` on success, or ``(None, 0)`` if the
    sidecar is missing (e.g. a report generated before this feature existed)
    so callers can warn and continue rather than crash. ``matched`` is
    ``_overlay_human_decisions``'s own count — the number of decisions that
    actually joined a group by ``group_hash`` — so a caller can tell "wrote a
    report" from "wrote a report that matched what it was handed": a code-review
    report whose groups carry no ``groupHash`` (F2) re-renders byte-identical
    with ``matched == 0`` and no error, which only the count exposes.
    """
    phase_dir = Path(phase_dir)
    sidecar = phase_dir / "report_data.json"
    if not sidecar.exists():
        return None, 0
    report_data = upgrade_legacy(json.loads(sidecar.read_text(encoding="utf-8")))
    matched = _overlay_human_decisions(report_data, human_decisions or {})
    # The commit guard's skips, read from the saved guard beside the
    # decisions (*guard*: the pinned record's ``guard``, None on a plan's run).
    _overlay_guard_skips(report_data, guard)
    style = template_style or report_data.get("templateStyle", "pr")
    template = _load_report_template(style)
    html = _embed_report_data(report_data, template)
    report_path = phase_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    # Keep the sidecar in sync so a subsequent re-run overlays cleanly.
    try:
        sidecar.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    except OSError:
        pass
    return report_path, matched


#: ``apply-code-fixes`` is the one apply phase whose mode word is not its
#: ``phase_name`` (the state.json key and phase-dir word the orchestrator
#: itself reads/writes through, e.g. ``ApplyCodeFixesOrchestrator.phase_name``
#: in ``apply_code_fixes_orchestrator.py``, ``"apply-fixes"``) — mirrors
#: ``full_workflow_orchestrator.WRITE_PHASE_DIRS`` and ``display_decisions
#: .resolve_output_file``'s ``phase_map``. ``apply-suggestions`` and
#: ``apply-task-suggestions`` need no entry: their mode word already equals
#: their phase_name.
_APPLY_PHASE_STATE_KEYS = {
    "apply-code-fixes": "apply-fixes",
}


def _read_human_decisions_from_state(
    state_file: Path, apply_phase: str
) -> Dict[str, Dict[str, Any]]:
    """Read ``human_decisions_{apply_phase}`` from a state.json file.

    ``apply_phase`` is normalized through ``_APPLY_PHASE_STATE_KEYS`` first, so
    a caller (the instructions, a human at the CLI) may pass either the mode
    word (``apply-code-fixes``) or the phase_name it is stored under
    (``apply-fixes``) and land on the same decisions.
    """
    state = upgrade_legacy(json.loads(Path(state_file).read_text(encoding="utf-8")))
    key_phase = _APPLY_PHASE_STATE_KEYS.get(apply_phase, apply_phase)
    return state.get(f"human_decisions_{key_phase}", {}) or {}


def _read_guard_from_state(state_file: Path) -> Optional[Dict[str, Any]]:
    """The commit apply guard saved in a state.json file (the pinned record's
    ``guard``, plans/review-commits.md §2.7), or None."""
    try:
        state = json.loads(Path(state_file).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(state, dict):
        return None
    # `commit_range.pinned_record`'s order, spelled here because this module
    # also runs as a direct script, where the package import is unavailable.
    for key in ("commit_range", "head_ref"):
        record = state.get(key)
        if isinstance(record, dict):
            guard = record.get("guard")
            return guard if isinstance(guard, dict) else None
    return None


def main(argv: Optional[List[str]] = None) -> int:
    """CLI: overlay recorded human decisions onto an existing review report."""
    bootstrap_streams()
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Regenerate an HTML review report with human/judge-agent decisions overlaid."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    rd = sub.add_parser(
        "regenerate-decisions",
        help="Overlay recorded human decisions onto an existing review report.html",
    )
    rd.add_argument(
        "--phase-dir",
        required=True,
        help="Review phase dir containing report_data.json / report.html",
    )
    rd.add_argument(
        "--state-file",
        required=True,
        help="state.json holding human_decisions_{apply-phase}",
    )
    rd.add_argument(
        "--apply-phase",
        required=True,
        help=(
            "Apply phase name, e.g. apply-suggestions / apply-code-fixes / "
            "apply-task-suggestions"
        ),
    )
    rd.add_argument(
        "--template-style",
        default=None,
        help="Override template style (pr/flat); defaults to the original style",
    )
    args = parser.parse_args(argv)

    if args.command == "regenerate-decisions":
        phase_dir = Path(args.phase_dir)
        decisions = _read_human_decisions_from_state(
            Path(args.state_file), args.apply_phase
        )
        guard = _read_guard_from_state(Path(args.state_file))
        if (not decisions and not (guard or {}).get("skipped")
                and (phase_dir / "report_data.json").exists()):
            # Live run 8 (Claude Code racing 05/08): a phase that decided
            # nothing by hand or by judge re-rendered the report anyway and
            # printed "0 of 0 human decision(s) matched", which the host
            # relayed. The executor leg's twin
            # (`ApplyOrchestratorBase.regenerate_decisions_overlay`) has
            # always left the report alone then; this leg now does too.
            print(
                f"No human or judge decisions are recorded for "
                f"{args.apply_phase}, so {phase_dir / 'report.html'} is left "
                "as it was."
            )
            return 0
        result, matched = regenerate_report_with_human_decisions(
            phase_dir, decisions, args.template_style, guard=guard
        )
        if result is None:
            print(
                f"No report_data.json in {phase_dir}; cannot overlay decisions "
                "(report predates the decision-overlay feature). Skipping HTML "
                "update."
            )
            return 0
        print(
            f"HTML report regenerated with {matched} of {len(decisions)} human "
            f"decision(s) matched: {result}"
        )
        if matched < len(decisions):
            print(
                f"WARNING: {len(decisions) - matched} decision(s) did not match "
                "any group in this report (no groupHash on the group, or the "
                "decision's id is stale). The report was still written.",
                file=sys.stderr,
            )
        return 0
    return 1


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
