#!/usr/bin/env python3
"""The published ``validation_context`` object: shape, aggregation, rendering.

A validation round embeds each context document (the plan, a review-tasks task
list, review-code's reviewed-code block, a code-fix diff) in one of three
modes, recorded per document as a *context source*:

* ``inline`` — the whole document fits under the inline limit and is in the
  prompt. Nothing is reported for it: a plan under the limit prints nothing and
  publishes nothing, as before.
* ``path`` — over the limit; the prompt keeps a head excerpt **and** names a
  hash-bound snapshot of the whole document by absolute path, which the
  validator is told to read. The excerpt is still an excerpt: ``chars`` is what
  was inlined, ``bytes`` the whole document. A host must never read ``path``
  as "the full document was inlined".
* ``truncated`` — over the limit and no readable snapshot (it could not be
  written, the runner cannot read files, or the source has no file at all).
  The prompt carries today's bare cut. This is the one mode that sets the
  result ``notice``.

This module is deliberately **stdlib-only and side-effect free**, because
``status`` (``utils/run_status.py``) renders the object and has to stay
sub-second: it must not import ``utils/validation.py``, which pulls in the
provider stack. The single writer of the key,
``utils.validation.publish_validation_context``, builds the object here too, so
the status file, the result line, the poll text and ``report.md`` all derive
from one shape and cannot disagree.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence

#: The three source modes, worst last. ``truncated`` outranks ``path`` outranks
#: ``inline`` wherever several records of one document (batches of a resumed
#: round) or several documents (the phase's top-level ``mode``) are combined.
MODE_INLINE = "inline"
MODE_PATH = "path"
MODE_TRUNCATED = "truncated"
MODE_RANK = {MODE_INLINE: 0, MODE_PATH: 1, MODE_TRUNCATED: 2}

#: The document labels a source may carry, in the order they are reported.
SOURCE_LABELS = ("plan", "tasks", "reviewed-code", "diff")

#: How the reason of a reviewed-code block whose implementation record was cut
#: starts. The notice carries that clause, because a record cut leaves no
#: dropped file and no char shortfall to show it by.
RECORD_CUT_REASON = "implementation record cut"

#: How a label reads inside a sentence.
_NOUN = {
    "plan": "the plan",
    "tasks": "the tasks file",
    "reviewed-code": "the reviewed code",
    "diff": "the diff",
}


def mode_rank(mode: Optional[str]) -> int:
    """Rank of ``mode`` (unknown words rank as ``inline``)."""
    return MODE_RANK.get(str(mode or MODE_INLINE), 0)


def worst_mode(modes: Iterable[Optional[str]]) -> str:
    """The worst of ``modes``; ``inline`` for an empty iterable."""
    worst = MODE_INLINE
    for mode in modes:
        if mode_rank(mode) > mode_rank(worst):
            worst = str(mode)
    return worst


def noun(label: Optional[str]) -> str:
    """How a source label reads inside a sentence (``the tasks file``)."""
    return _NOUN.get(str(label or ""), f"the {label or 'context'}")


def _status_entry(record: Dict[str, Any]) -> Dict[str, Any]:
    """One ``validation_context.sources`` entry from one context source record.

    The status shape is the documented one (``label``, ``mode``, ``chars``,
    ``path``, ``sha256``, ``dropped_sections``) plus the fields the renderers
    need to say *how much* was shown — ``bytes`` (the whole document),
    ``sections_total``/``sections_shown`` and a ``reason`` for a truncation.
    """
    entry: Dict[str, Any] = {
        "label": record.get("label"),
        "mode": record.get("mode", MODE_INLINE),
        "chars": record.get("chars_shown", record.get("chars")),
        "bytes": record.get("bytes"),
        "path": record.get("abs_path", record.get("path")),
        "sha256": record.get("sha256"),
        "dropped_sections": list(record.get("dropped_sections") or []),
    }
    for key in ("sections_total", "sections_shown", "reason", "dropped_files"):
        if record.get(key) is not None:
            entry[key] = record[key]
    return entry


def aggregate_sources(
    records: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """One status entry per document label, worst mode and smallest ``chars`` wins.

    Batches of one round embed the same excerpt, so their records for one
    document agree; a resumed round may mix, and then the entry takes the worst
    mode (and that mode's own path/reason) and the smallest excerpt, so the
    report can only understate what a validator saw.
    """
    by_label: Dict[str, Dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not record.get("label"):
            continue
        entry = _status_entry(record)
        label = str(entry["label"])
        current = by_label.get(label)
        if current is None:
            by_label[label] = entry
            continue
        chars = [c for c in (current.get("chars"), entry.get("chars")) if isinstance(c, int)]
        if mode_rank(entry["mode"]) > mode_rank(current["mode"]):
            current, entry = entry, current
            by_label[label] = current
        if chars:
            current["chars"] = min(chars)
    order = {label: i for i, label in enumerate(SOURCE_LABELS)}
    return [
        by_label[label]
        for label in sorted(by_label, key=lambda l: (order.get(l, len(order)), l))
    ]


def build_validation_context(
    *,
    phase: Optional[str],
    sources: Iterable[Dict[str, Any]],
    limit: int,
    insufficient: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """The published object, or ``None`` when every source is ``inline``.

    ``None`` is the invalidation rule: a round whose documents all fit inline
    publishes nothing, and the writer removes any earlier round's key.
    """
    entries = aggregate_sources(sources)
    if not entries or all(e["mode"] == MODE_INLINE for e in entries):
        return None
    return {
        "phase": phase,
        "limit": limit,
        "mode": worst_mode(e["mode"] for e in entries),
        "insufficient": int(insufficient or 0),
        "sources": entries,
    }


def _shown_phrase(entry: Dict[str, Any]) -> str:
    """``8 of 20 sections`` / ``60000 of 108225 chars`` / cited-file wording."""
    total = entry.get("sections_total")
    shown = entry.get("sections_shown")
    if isinstance(total, int) and total > 0 and isinstance(shown, int):
        unit = "cited files" if entry.get("label") == "reviewed-code" else "sections"
        return f"{shown} of {total} {unit}"
    chars = entry.get("chars")
    size = entry.get("bytes")
    if isinstance(chars, int) and isinstance(size, int) and size > chars:
        return f"{chars} of {size} chars"
    if isinstance(chars, int) and isinstance(size, int) and size > 0:
        # The block was cut before it was measured (review-code's record), so
        # "N of N chars" would read as "all of it"; the reason says what went.
        return f"{chars} chars"
    if isinstance(chars, int):
        return f"the first {chars} chars"
    return "part"


def truncation_sentence(entry: Dict[str, Any]) -> str:
    """The notice sentence for one ``truncated`` source."""
    sentence = f"Validation saw {_shown_phrase(entry)} of {noun(entry.get('label'))}"
    dropped_files = entry.get("dropped_files")
    if dropped_files:
        sentence += f" (dropped: {', '.join(str(f) for f in dropped_files)})"
    reason = entry.get("reason")
    if isinstance(reason, str):
        for part in reason.split("; "):
            if part.startswith(RECORD_CUT_REASON):
                sentence += f" ({part})"
    return sentence


def validation_context_notice(obj: Optional[Dict[str, Any]]) -> Optional[str]:
    """The truncation notice for a published object, or ``None``.

    Only a ``truncated`` source sets one; a ``path`` source carries the whole
    document by path and sets none. Several truncated sources join with
    ``"; "`` in label order.
    """
    if not isinstance(obj, dict):
        return None
    sentences = [
        truncation_sentence(entry)
        for entry in obj.get("sources") or []
        if isinstance(entry, dict) and entry.get("mode") == MODE_TRUNCATED
    ]
    return "; ".join(sentences) or None


def source_phrase(entry: Dict[str, Any]) -> str:
    """How one source reads in the status text and the report header.

    ``path`` always says *excerpt plus path*, never "full plan inlined".
    """
    label = entry.get("label") or "context"
    mode = entry.get("mode")
    chars = entry.get("chars")
    excerpt = f"{chars}-char excerpt" if isinstance(chars, int) else "excerpt"
    if mode == MODE_PATH:
        return f"{label}: {excerpt} inline + full snapshot by path ({entry.get('path')})"
    if mode == MODE_TRUNCATED:
        text = f"{label}: TRUNCATED, {_shown_phrase(entry)} shown inline, no readable file"
        if entry.get("reason"):
            text += f" ({entry['reason']})"
        return text
    return f"{label}: inline in full"


def validation_context_text(obj: Optional[Dict[str, Any]]) -> Optional[str]:
    """One rendered line for the status view / report header, or ``None``."""
    if not isinstance(obj, dict) or not obj.get("sources"):
        return None
    phase = obj.get("phase")
    parts = [source_phrase(e) for e in obj["sources"] if isinstance(e, dict)]
    head = f"validation context ({phase}): " if phase else "validation context: "
    line = head + "; ".join(parts)
    insufficient = obj.get("insufficient")
    if isinstance(insufficient, int) and insufficient > 0:
        line += (
            f"; {insufficient} verdict(s) answered insufficient-context "
            f"(the validator could not read the snapshot)"
        )
    return line


def pick_worst(objects: Sequence[Optional[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    """The object with the worst top-level ``mode``; first in order on a tie."""
    best: Optional[Dict[str, Any]] = None
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if best is None or mode_rank(obj.get("mode")) > mode_rank(best.get("mode")):
            best = obj
    return best


def report_header_lines(obj: Optional[Dict[str, Any]]) -> List[str]:
    """``report.md`` header lines for a published object; ``[]`` when absent.

    Rendered from the object ``.status.json`` holds — the report never
    recomputes modes — so the report, the poll text and ``MULTI_LLM_RESULT``
    agree. One ``**Validation context:**`` line (the status text minus its
    ``validation context (<phase>): `` head) and, when a source is
    ``truncated``, one ``**Validation context warning:**`` line carrying the
    notice sentence. No object → no lines, so the report is byte-identical to
    one written before the key existed.
    """
    text = validation_context_text(obj)
    if not text or not isinstance(obj, dict):
        return []
    phase = obj.get("phase")
    head = f"validation context ({phase}): " if phase else "validation context: "
    if text.startswith(head):
        text = text[len(head):]
    lines = [f"**Validation context:** {text}"]
    notice = validation_context_notice(obj)
    if notice:
        lines.append(f"**Validation context warning:** {notice}")
    return lines


__all__ = [
    "MODE_INLINE",
    "MODE_PATH",
    "MODE_TRUNCATED",
    "MODE_RANK",
    "RECORD_CUT_REASON",
    "SOURCE_LABELS",
    "aggregate_sources",
    "build_validation_context",
    "mode_rank",
    "noun",
    "pick_worst",
    "report_header_lines",
    "source_phrase",
    "truncation_sentence",
    "validation_context_notice",
    "validation_context_text",
    "worst_mode",
]
