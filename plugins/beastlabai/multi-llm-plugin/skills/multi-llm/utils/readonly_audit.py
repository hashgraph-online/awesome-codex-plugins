"""The read-only stream audit's verdict type, its AND-combination, and its switch.

Plan ``validation-context-by-path-and-codex-0156-fallout`` §4, option B. An
uncontained slot (the ``danger-full-access`` rung) is bracketed by the porcelain
detective check (``review_orchestrator_base.porcelain_snapshot``). That check
sees *that* the tree changed during the slot's window, never *who* changed it,
so on run ``0c477c4d`` it discarded a codex review for two paths another session
in the same repository was editing. Option B reads the slot's own structured
action stream instead: when every tool action the runner reports is provably
read-only, a porcelain delta cannot be this slot's, and the check is downgraded
to a ``not attributed`` warning.

What lives here is the provider-neutral half:

- :class:`AuditVerdict`, the compact verdict an adapter's
  ``audit_readonly_stream`` hook returns. Only this rides out of
  ``llm_client`` (as ``details['readonly_audit']``, via :meth:`to_dict`); the
  raw stream never does.
- :func:`combine_audits`, the AND across every attempt in a slot's snapshot
  window. A missing verdict (``None``: the adapter has no opinion, the attempt
  never spawned, the envelope lost it) makes the combination non-clean.
- :data:`STREAM_AUDIT_EXEMPTION_ENABLED`, the one switch that lets a clean
  combination actually change a verdict. See its comment.

The codex classifier itself is ``utils/providers/codex_stream_audit.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional

#: THE SWITCH. ``True`` = a clean combination of every attempt's stream audit
#: downgrades a porcelain delta on an uncontained codex slot to a
#: ``not attributed`` warning; any non-clean or missing verdict keeps the
#: fail-closed verdict. ``False`` restores the pre-plan behaviour: the audit is
#: still computed and recorded on every codex attempt, but changes nothing.
#:
#: Enabled 2026-09-25, after the §6.2 live capture (plan §4.2 step 5 and §6.2;
#: see plans/validation-context-by-path-and-codex-0156-fallout.md, Implementation
#: Notes "§6.2 live capture (2026-09-25)"): the web-search capture landed
#: (``tests/fixtures/codex/0.156.1/web_search_*``), the classifier names
#: ``search`` / ``open_page`` / ``find_in_page`` / ``other`` and
#: ``text_result`` inert from it, and run ``0c477c4d``'s acceptance stream
#: audits clean.
STREAM_AUDIT_EXEMPTION_ENABLED = True

#: ``details`` key the verdict travels on, out of ``llm_client``.
DETAILS_KEY = "readonly_audit"


@dataclass(frozen=True)
class AuditVerdict:
    """One attempt's read-only verdict, computed on its full in-memory stream.

    ``clean`` is True only when the stream completed (``turn.completed``), every
    action it started also completed, and every action item was classified
    read-only. ``reason`` names the first thing that failed it (an item id and a
    category, never the command text or its output); it is ``""`` when clean.
    ``actions`` counts the tool-action items the audit classified.
    """

    clean: bool
    reason: str = ""
    actions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"clean": bool(self.clean), "reason": self.reason,
                "actions": int(self.actions)}


def _as_mapping(verdict: Any) -> Optional[Mapping[str, Any]]:
    if isinstance(verdict, AuditVerdict):
        return verdict.to_dict()
    if isinstance(verdict, Mapping):
        return verdict
    return None


def combine_audits(verdicts: Iterable[Any]) -> AuditVerdict:
    """AND every attempt's verdict in one slot's snapshot window (plan 4.3).

    Clean only if there was at least one attempt and **every** attempt carried a
    verdict whose ``clean`` is exactly ``True``. A clean last attempt never
    excuses an earlier attempt that wrote, was incomplete, or recorded nothing.
    """
    seen = 0
    actions = 0
    for index, raw in enumerate(verdicts, start=1):
        seen += 1
        verdict = _as_mapping(raw)
        if verdict is None:
            return AuditVerdict(False, f"attempt {index}: no audit verdict recorded")
        if verdict.get("clean") is not True:
            why = verdict.get("reason") or "not clean"
            return AuditVerdict(False, f"attempt {index}: {why}")
        try:
            actions += int(verdict.get("actions") or 0)
        except (TypeError, ValueError):
            pass
    if not seen:
        return AuditVerdict(False, "no attempt carried an audit verdict")
    return AuditVerdict(True, "", actions)


def exemption_applies(verdicts: Iterable[Any]) -> bool:
    """Whether a porcelain delta may be downgraded to a ``not attributed`` warning.

    True only while :data:`STREAM_AUDIT_EXEMPTION_ENABLED` is on AND the
    combination of every attempt's verdict is clean. Read at call time (never
    captured at import) so a test can flip the switch with ``monkeypatch``.
    """
    if not STREAM_AUDIT_EXEMPTION_ENABLED:
        return False
    return combine_audits(verdicts).clean


def describe(verdict: Any) -> str:
    """One short line for a log header: ``clean (N actions)`` / ``not clean: …``."""
    mapping = _as_mapping(verdict)
    if mapping is None:
        return "none"
    if mapping.get("clean") is True:
        return f"clean ({mapping.get('actions', 0)} action(s))"
    return f"not clean: {mapping.get('reason') or 'unspecified'}"
