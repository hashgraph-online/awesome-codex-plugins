"""The judge's persisted vocabulary, and the one place its old spellings are read.

The judge that decides ``needs-human-decision`` items under ``--agent-decide``
(and salvages them) is whatever agent the host runs: Claude Code's own agent, a
``codex:<chat model>`` session, an opencode model. Until 2026-10-02 every key and
marker it left on disk was nonetheless spelled ``claude_*`` — the racing run's
Codex leg judged with ``codex:gpt-6-astra`` and persisted
``source: claude_auto_decide`` beside ``[claude_skipped]`` (issue 18 of
plans/2026-10-01-three-host-racing-run.md). Everything below is the host-neutral
spelling, and **writers use only these names**.

**Readers accept both.** A ``state.json`` from an in-progress run, an existing
review folder's ``user_selections.json``, an ``orchestrator_output.json`` or a
``report_data.json`` sidecar written before the rename must load and behave
exactly as before, and ``--resume`` must cross the upgrade. The legacy spellings
are therefore mapped here and nowhere else: :data:`LEGACY_VALUES` and
:data:`LEGACY_KEYS` are the whole table, :func:`canonical_value` is the per-value
reader and :func:`upgrade_legacy` rewrites a loaded document once at its load
boundary. A writer that re-saves an upgraded document (``StateManager.save``)
therefore writes only the new names, and ``StateManager`` writes an upgrade
back at load even when nothing saves after it, because the host reads
``state.json`` raw.

Old batch ids (``claude_decide_<hash>``) are deliberately *not* rewritten: a
``batch_id`` is an opaque identifier nothing parses, and only new ids get the
:data:`JUDGE_BATCH_ID_PREFIX`.
"""

from __future__ import annotations

from typing import Any, Dict

__all__ = [
    "JUDGE_DECIDE",
    "JUDGE_AUTO_DECIDE",
    "JUDGE_AUTO_DECIDE_SALVAGE",
    "JUDGE_SKIPPED",
    "JUDGE_DECIDE_ITEM_IDS",
    "JUDGE_DECIDED",
    "JUDGE_BATCH_ID_PREFIX",
    "LEGACY_VALUES",
    "LEGACY_KEYS",
    "canonical_value",
    "upgrade_legacy",
]

#: The override value a reviewer picks for "Let the agent decide" (report.md,
#: ``user_selections.json``, ``consolidated_user_selections.json``) and the
#: routing flag it sets on a group or suggestion. A marker, never a status.
JUDGE_DECIDE = "judge_decide"

#: ``human_review_config.decision_mode`` under ``--agent-decide``, the per-item
#: ``decision_mode`` of a pre-marked item, and a judged decision's
#: ``batch_context.decision_source`` / ``batch_action``.
JUDGE_AUTO_DECIDE = "judge_auto_decide"

#: ``decision_source`` / ``batch_action`` of a salvaged item (recorded as
#: ``approved``; this marker is what says it was salvaged).
JUDGE_AUTO_DECIDE_SALVAGE = "judge_auto_decide_salvage"

#: ``skipped_items[].status`` of an item the judge skipped.
JUDGE_SKIPPED = "judge_skipped"

#: The ``human_review_config`` key listing the items pre-marked for the judge.
JUDGE_DECIDE_ITEM_IDS = "judge_decide_item_ids"

#: The ``report_data.json`` key (on ``humanDecision`` and in
#: ``humanDecisionsSummary``) for "the judge made this decision".
JUDGE_DECIDED = "judgeDecided"

#: Prefix of a judged batch's ``batch_id``.
JUDGE_BATCH_ID_PREFIX = "judge_decide_"

#: Legacy string value -> its host-neutral spelling. Matched exactly, never as
#: a substring, so free text that merely mentions one is left alone.
LEGACY_VALUES: Dict[str, str] = {
    "claude_decide": JUDGE_DECIDE,
    "claude_auto_decide": JUDGE_AUTO_DECIDE,
    "claude_auto_decide_salvage": JUDGE_AUTO_DECIDE_SALVAGE,
    "claude_skipped": JUDGE_SKIPPED,
}

#: Legacy mapping key -> its host-neutral spelling.
LEGACY_KEYS: Dict[str, str] = {
    "claude_decide": JUDGE_DECIDE,
    "claude_decide_item_ids": JUDGE_DECIDE_ITEM_IDS,
    "claudeDecided": JUDGE_DECIDED,
}


def canonical_value(value: Any) -> Any:
    """*value* with a legacy judge spelling replaced; anything else unchanged."""
    if isinstance(value, str):
        return LEGACY_VALUES.get(value, value)
    return value


def upgrade_legacy(document: Any) -> Any:
    """*document* with every legacy judge key and value renamed, in place.

    Walks dicts and lists recursively. A legacy key is renamed; when the new
    key is already present only one survives, so a half-upgraded document
    never carries both. The new one wins, unless it is empty or falsy (``[]``,
    ``None``, ``False``, ``0``) while the legacy one is not: that is a default
    some writer filled in over an old document, and keeping it would erase
    what the old key recorded. String values are mapped through
    :func:`canonical_value`. Returns *document* so a loader can write
    ``data = upgrade_legacy(json.load(f))``.
    """
    if isinstance(document, dict):
        for key in list(document):
            value = document[key]
            new_key = LEGACY_KEYS.get(key, key) if isinstance(key, str) else key
            if new_key != key:
                del document[key]
                if new_key in document and (document[new_key] or not value):
                    continue
            if isinstance(value, (dict, list)):
                upgrade_legacy(value)
            else:
                value = canonical_value(value)
            document[new_key] = value
    elif isinstance(document, list):
        for index, value in enumerate(document):
            if isinstance(value, (dict, list)):
                upgrade_legacy(value)
            else:
                document[index] = canonical_value(value)
    return document
